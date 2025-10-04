from __future__ import annotations

# Standard typing
from typing import Literal, TypedDict, Annotated

# LangChain / LangGraph core
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.types import Command
from langgraph.graph.message import add_messages
from langgraph.graph import END
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
load_dotenv()

# Project modules
from retriever import (
    extract_text_auto,
    chunk_document_text,
    get_relevant_chunks,
)
from tools import laws_db_lookup, procedures_db_lookup, generate_court_form



class Router(TypedDict):
    next: Literal["law", "procedure", "general", "FINISH"]

class State(TypedDict):
    messages: Annotated[list, add_messages]
    next: str
    file_path: str | None
    extracted_context: str | None


LAW_SYS = (
    f"""Role: Senior Legal Analyst Specializing in Legislative Frameworks & Statutory Interpretation\n
    To provide accurate, accessible, and contextually nuanced explanations of Acts of Parliament, regulations, and statutory instruments.
    If a user provides a document (image/pdf), text will be extracted using OCR and PDF parsing before proceeding. Use that as context of query and reply to that query with respect to that.
    This includes clarifying legislative intent, assisting in statutory interpretation, comparing similar legal provisions,
    and guiding users through the procedural and practical applications of laws in diverse jurisdictions.
    
    IMPORTANT: Call laws_db_lookup EXACTLY ONCE with the most relevant query, then provide your complete answer based on those results.

    Use the laws_db_lookup tool to extract and analyze the relevant legislative or statutory content required to address the. 
    
    Carefully interpret the legal text using the appropriate method of statutory interpretation (e.g., literal rule, golden rule, mischief rule, purposive approach).
    Summarize your findings using a structure defined in agent_knowledge_context. Break down the meaning 
    in plain English to make the law accessible to users who may not have legal training. Ensure citations 
    are provided where applicable (section numbers, case law, jurisdictional references).
    Structured legal response including:\n"
            "- Summary of relevant legislation or statutory rule(s) in Plain English interpretation of the provision\n"
            "- Statutory interpretation method used and justification\n"
            "- Citation of legal sources (e.g., section numbers, cases)\n"
            "- Final conclusion or recommendation")"""
)

PROC_SYS = (
    """You are a legal documentation expert for Victorian court procedures.

CRITICAL INSTRUCTION FOR FORM GENERATION:
When the user's message contains ANY of these words: "generate", "create", "make", "need a form", "prepare a form":
YOU MUST CALL THE generate_court_form TOOL. DO NOT just describe the form.

Steps you MUST follow:
1. First, use procedures_db_lookup to get form requirements (if needed)
2. Then IMMEDIATELY call generate_court_form with proper form_data
3. After calling the tool, tell the user the form was generated

Example of calling generate_court_form:
{{
    "title": "NOTICE OF OPPOSITION TO APPLICATION OTHER THAN FOR LEAVE TO APPEAL",
    "subtitle": "Supreme Court of Victoria",
    "fields": ["Case Number", "Applicant's Name", "Respondent's Name", "Date of Filing", "Details of Opposition", "Grounds for Opposition", "Supporting Documents", "Contact Information"],
    "instructions": "1. Complete all fields\\n2. File in person or via e-filing\\n3. Attach supporting documents\\n4. Pay relevant court fees"
}}

For non-form questions: Use procedures_db_lookup to provide procedural guidance.

REMEMBER: If user asks to GENERATE/CREATE a form, you MUST use the generate_court_form tool!"""
)

UNKNOWN_SYS = (
    f"""You are Lexi, a friendly legal assistant. you handle user :\n
    'I am your legal assistant named Lexi. I help with interpreting Victorian laws and court procedures.'\n
    Handle casual questions and simple legal curiosities in plain English. If the question should be routed
    to law/procedure for deeper detail, suggest a better phrasing. Be concise and helpful."""
)



members = ["law", "procedure", "general"]
SUPERVISOR_AGENT_PROMPT = f"""You are the routing supervisor for a legal assistant named Lexi.
                            ANALYZE THE USER'S QUESTION AND RESPOND WITH EXACTLY ONE WORD FROM: law, procedure, general:
                              {members}.

                              Route to 'law' if the question:
                                - Asks about interpreting Acts, legislation, or regulations
                                - Requires understanding statutory provisions or acts
                                - Seeks explanation of legal concepts from legislation
                                - Involves criminal charges or offenses
                                - Questions about legal liability or penalties

                                Route to 'procedure' if the question:
                                - Asks about how to file or prepare legal documents
                                - Involves court forms, applications, or submissions
                                - Requests guidance on court processes or deadlines

                                Route to 'general' if the question:
                                - Is a greeting or asks about capabilities
                                - Seeks very basic legal information
                                - Is general conversation

                                RESPOND WITH ONLY ONE WORD: law, procedure, or general"""

llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0,streaming=True)

law_agent = create_react_agent(
    model="gpt-4o-mini",
    tools=[laws_db_lookup],
    prompt =SystemMessage(LAW_SYS),       
)
procedure_agent = create_react_agent(
    model="gpt-4o-mini",
    tools=[procedures_db_lookup,generate_court_form],
    prompt =SystemMessage(PROC_SYS),
)
general_agent = create_react_agent(
    model="gpt-4.1-nano",
    tools=[],
    prompt = SystemMessage(UNKNOWN_SYS)
)


def supervisor_node(state: State,file_path: str = None) -> Command[Literal["law", "procedure", "general", "__end__"]]:
    extracted_context = None
    file_path = state["file_path"]
    if file_path:
        # Extract and chunk text
        extracted_text = extract_text_auto(file_path)
        chunks = chunk_document_text(extracted_text)
        
        # Get relevant chunks based on user query
        relevant_text = get_relevant_chunks(chunks, state["messages"][-1].content)
        extracted_context = relevant_text

    messages = [
        {"role": "system", "content": SUPERVISOR_AGENT_PROMPT},
        {"role": "user", "content": f"Route this question: {state['messages'][-1].content}"}
    ]
    
    response = llm.invoke(messages)
    decision = response.content.strip().lower()

    # print(f"Supervisor decision: {decision}")
    
    # Map the decision to a destination
    if decision == "finish":
        goto = END
    elif decision in ["law", "procedure", "general"]:
        goto = decision
    else:
        goto = "general"

    return Command(goto=goto, update={
        "extracted_context": extracted_context,
        "next": goto
        })


def law_node(state: State) -> Command[Literal["supervisor"]]:
    print("invoke law agent")
    user_query = state["messages"][-1].content
    if state.get("extracted_context"):
        enhanced_query = f"""User question: {user_query}
                            User question context document:
                            {state['extracted_context']}"""
        temp_messages = state["messages"][:-1] + [HumanMessage(content=enhanced_query)]
        temp_state = {**state, "messages": temp_messages}
        result = law_agent.invoke(temp_state)
    else:
        result = law_agent.invoke(state)
    
    return Command(
        update = {
            "messages" : [AIMessage(content = result["messages"][-1].content)]
        },
        goto = END
    )

def procedure_node(state: State) -> Command[Literal["supervisor"]]:
    print("Invoke procedure")
    user_query = state["messages"][-1].content
    if state.get("extracted_context"):
        enhanced_query = f"""User question: {user_query}
                            User question context document:
                            {state['extracted_context']}"""
        temp_messages = state["messages"][:-1] + [HumanMessage(content=enhanced_query)]
        temp_state = {**state, "messages": temp_messages}
        result = procedure_agent.invoke(temp_state)
    else:
        result = procedure_agent.invoke(state)
        
    return Command(
        update = {
            "messages" : [AIMessage(content = result["messages"][-1].content)]
        },
        goto = END
    )

def general_node(state: State) -> Command[Literal["supervisor"]]:
    print("invoke general agent")
    result = general_agent.invoke(state)
    return Command(
        update = {
            "messages" : [AIMessage(content = result["messages"][-1].content)]
        },
        goto = END
    )

def router(state: State) -> Literal["law", "procedure", "unknown"]:
    return state["route"]