import os
import sys
import uuid
import tempfile
import streamlit as st
import time
import threading
from phoenix.otel import register   #type: ignore
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports (must be before auth import)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import authentication module
from auth import SessionManager, render_auth_page

def load_main_application():
    """Load the main application after authentication."""
    
    # Phoenix tracing setup (must be before other imports)
    

    phoenix_headers = {
        "api-key": os.environ.get("ARIZE_PHNX"),
        "Authorization": f"Bearer {os.environ.get('ARIZE_PHNX')}",
    }

    tracer_provider = register(
        project_name="lexilaw_agent",
        endpoint="https://app.phoenix.arize.com/s/rajatsharma786-rs/v1/traces",
        headers=phoenix_headers,
        auto_instrument=True,
    )

    from agent_flow_calling import build_app, call_multi_agent_system

    # =============================================================================
    # Streamlit Configuration (reconfigure for main app)
    # =============================================================================
    st.set_page_config(
        page_title="Lexi Law Agent",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    # Custom CSS for fixed bottom input
    st.markdown("""
    <style>
    /* Add padding to main container so content doesn't hide behind fixed input */
    /* Professional Markdown Styling - All text white */
    .stChatMessage {
        font-family: 'Inter', 'Segoe UI', 'Arial', 'sans-serif' !important;
        font-size: 1.08rem !important;
        color: #fff !important;
        background: none !important;
        font-weight: 400 !important;
    }
    .stChatMessage h1, .stChatMessage h2, .stChatMessage h3 {
        font-weight: 600 !important; /* Reduce boldness */
        font-size: 1.5rem !important; /* Adjust size */
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stChatMessage p, .stChatMessage li, .stChatMessage td, .stChatMessage th {
        color: #fff !important;
        font-weight: 400 !important;
    }
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stChatMessage th, .stChatMessage td {
        border: 1px solid #e5e7eb !important;
        padding: 0.75rem !important;
        text-align: left !important;
    }
    
    .stChatMessage th {
        background-color: rgba(30, 30, 40, 0.5) !important;
        font-weight: 600 !important;
        color: #fff !important;
    }
    
    .stChatMessage tr:nth-child(even) {
        background-color: rgba(30, 30, 40, 0.3) !important;
    }
    
    /* Strong/bold text styling */
    .stChatMessage strong, .stChatMessage b {
        color: #fff !important;
        font-weight: 600 !important;
    }
    
    /* Emphasis/italic styling */
    .stChatMessage em, .stChatMessage i {
        color: #fff !important;
        font-style: italic !important;
    }
    
    /* Link styling */
    .stChatMessage a {
        color: #fff !important;
        text-decoration: none !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.5) !important;
        transition: border-bottom-color 0.2s ease !important;
    }
    
    .stChatMessage a:hover {
        border-bottom-color: #2563eb !important;
    }
    
    /* Horizontal rule styling */
    .stChatMessage hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(to right, rgba(255, 255, 255, 0.5), transparent) !important;
        margin: 2rem 0 !important;
    }
    
    /* Special legal document styling */
    .stChatMessage .legal-section {
        background-color: rgba(20, 20, 30, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        color: #fff !important;
    }
    
    /* Citation styling */
    .stChatMessage .citation {
        background-color: rgba(30, 30, 40, 0.3) !important;
        border-left: 4px solid rgba(255, 255, 255, 0.5) !important;
        padding: 0.75rem 1rem !important;
        margin: 1rem 0 !important;
        border-radius: 0 4px 4px 0 !important;
        font-size: 0.95rem !important;
        color: #fff !important;
    }

    /* Adjust heading sizes and weights */
    .stChatMessage h1, .stChatMessage h2, .stChatMessage h3 {
        font-weight: 600 !important; /* Reduce boldness */
        font-size: 1.5rem !important; /* Adjust size */
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Ensure uploaded images are cleared properly */
    .stChatMessage img {
        display: none !important; /* Hide images after use */
    }
    </style>
    """, unsafe_allow_html=True)
    
    # =============================================================================
    # Session State Initialization
    # =============================================================================
    # Get authenticated user data
    user_data = SessionManager.get_current_user()
    
    # Use username as thread_id for personalized sessions
    if "thread_id" not in st.session_state or st.session_state.thread_id != user_data['username']:
        st.session_state.thread_id = user_data['username']
        # Clear chat history when switching users
        st.session_state.chat_history = []

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "app" not in st.session_state:
        with st.spinner("🔄 Initializing Lexi Law Agent..."):
            st.session_state.app = build_app()

    # =============================================================================
    # Sidebar
    # =============================================================================
    with st.sidebar:
        st.title("⚖️ Lexi Settings")
        
        # User info section
        user_data = SessionManager.get_current_user()
        if user_data:
            st.success(f"👋 Welcome, **{user_data['username']}**!")
            st.caption(f"📧 {user_data['email']}")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                SessionManager.logout_user()
                st.rerun()
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.chat_history = []
            # Keep the same thread_id (username) but clear the conversation
            st.rerun()
        
        st.markdown("---")
        
        # About section
        st.subheader("ℹ️ About Lexi")
        st.markdown("""
        Lexi is your AI legal assistant specializing in:
        
        - 📚 **Victorian Laws**: Interpretation of Acts, regulations, and statutory instruments
        - 📝 **Court Procedures**: Guidance on court forms and processes
        - 💡 **General Legal Info**: Answering basic legal questions
        
        """)
        
        st.markdown("---")
        
        # Environment status
        st.subheader("🔧 System Status")
        redis_status = "✅ Connected" if os.environ.get("REDIS_HOST") else "❌ Not configured"
        openai_status = "✅ Configured" if os.environ.get("OPENAI_API_KEY") else "❌ Not configured"
        phoenix_status = "✅ Enabled" if os.environ.get("ARIZE_PHNX") else "❌ Not configured"
        
        st.caption(f"**Redis:** {redis_status}")
        st.caption(f"**OpenAI:** {openai_status}")
        st.caption(f"**Phoenix:** {phoenix_status}")
        
        st.markdown("---")

    # =============================================================================
    # Helper Functions
    # =============================================================================
    def save_uploaded_file(uploaded_file) -> str | None:
        """Save uploaded file to temp directory and return path."""
        if not uploaded_file:
            return None
        
        suffix = os.path.splitext(uploaded_file.name)[1]
        tmp_path = os.path.join(
            tempfile.gettempdir(),
            f"lexi_{uuid.uuid4().hex}{suffix}"
        )
        
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return tmp_path

    def _strip_agent_prefix(text: str) -> str:
        """Remove agent-name prefixes (case-insensitive)."""
        if not isinstance(text, str) or not text:
            return text
        
        text = text.strip()
        
        # Method 1: Check if first word is an agent name
        words = text.split(maxsplit=1)
        if words and words[0].lower() in {"general", "law", "procedure"}:
            return words[1] if len(words) > 1 else ""
        
        # Method 2: Check for punctuation-based prefixes
        prefixes = [
            "general!", "general:", "general ",
            "law!", "law:", "law ",
            "procedure!", "procedure:", "procedure "
        ]
        
        text_lower = text.lower()
        for prefix in prefixes:
            if text_lower.startswith(prefix):
                return text[len(prefix):].strip()
        
        return text


    # =============================================================================
    # Main Chat Interface
    # =============================================================================
    st.title("⚖️ Lexi Law Agent")
    st.caption("Your AI assistant for Victorian laws and court procedures")

    for role, content in st.session_state.chat_history:
        with st.chat_message(role):
            # Use the helper to clean any prefixes in history too
            clean_content = _strip_agent_prefix(content) if isinstance(content, str) else content
            st.markdown(clean_content)

    st.markdown("---")


    # =============================================================================
    # Input Section - MUST BE AT THE VERY END
    # =============================================================================

    col1, col2 = st.columns([0.05, 0.95])

    uploaded_file = None

    # Initialize file uploader key if not present
    if "file_uploader_key" not in st.session_state:
        st.session_state.file_uploader_key = 0
        
    # Ensure clear_file_flag is initialized
    if "clear_file_flag" not in st.session_state:
        st.session_state.clear_file_flag = False
        
    # Reset file uploader when a new message is sent (increment key to force refresh)
    if st.session_state.get("clear_file_flag", False):
        st.session_state.file_uploader_key += 1
        st.session_state.clear_file_flag = False

    with col1:
        with st.popover("➕"):
            file_obj = st.file_uploader(
                "Attach Document",
                type=["pdf", "png", "jpg", "jpeg"],
                label_visibility="collapsed",
                key=f"file_uploader_{st.session_state.file_uploader_key}",
                help="Max 200MB - PDF, PNG, JPG, JPEG"
            )
            if file_obj:
                uploaded_file = file_obj
                st.success(f"📄 {file_obj.name}")
                st.caption(f"Size: {file_obj.size / 1024:.1f} KB")

    with col2:
        prompt = st.chat_input("Ask me anything about Victorian laws or court procedures...")

    # =============================================================================
    # Message Processing
    # =============================================================================
    if prompt:
        # Add user message to history
        st.session_state.chat_history.append(("user", prompt))
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Save uploaded file if present
        file_path = save_uploaded_file(uploaded_file)

        # Display assistant response with streaming
        with st.chat_message("assistant"):
            response_placeholder = st.empty()

            # Use a mutable container for accumulation
            response_container = {"text": "", "stop_loading": False,"filtered_start": False}

            # Simpler loading messages without markdown formatting issues
            loading_messages = [
                "⚖️ Lexi is analyzing your question...",
                "📚 Searching legal databases...",
                "🔍 Reviewing relevant statutes...",
                "💡 Formulating response..."
            ]

            loading_container = st.empty()

            def on_token(token: str):
                # stop loading on first token
                if not response_container["text"]:
                    response_container["stop_loading"] = True

                response_container["text"] += token

                # Filter prefix once, at the start of streaming
                display_text = response_container["text"]
                if not response_container["filtered_start"] and display_text.strip():
                    cleaned = _strip_agent_prefix(display_text)
                    if cleaned != display_text:
                        response_container["text"] = cleaned
                        display_text = cleaned
                    response_container["filtered_start"] = True

                response_placeholder.markdown(display_text)

            try:
                # Use the streaming function with callback
                full_response = call_multi_agent_system(
                    agent=st.session_state.app,
                    prompt=prompt,
                    userid=st.session_state.thread_id,
                    file_path=file_path,
                    on_token=on_token
                )

                # Ensure loading stops
                response_container["stop_loading"] = True
                time.sleep(0.1)  # Give thread time to clean up
                loading_container.empty()

                clean_final = _strip_agent_prefix(full_response).strip()

                # Check for PDF generation and extract file path
                if ".pdf" in full_response:
                    st.success("✅ Form generated successfully!")
                    
                    # Extract the PDF file path from the response
                    # Look for file paths in the response (e.g., C:\Users\...\file.pdf or /tmp/file.pdf)
                    import re
                    pdf_path_match = re.search(r'([A-Za-z]:\\[^\s]+\.pdf|/[^\s]+\.pdf)', full_response)
                    
                    if pdf_path_match:
                        pdf_path = pdf_path_match.group(1)
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=pdf_data,
                                    file_name=os.path.basename(pdf_path),
                                    mime="application/pdf",
                                    key=f"download_pdf_{st.session_state.thread_id}_{len(st.session_state.chat_history)}"
                                )

                # Final display (ensure complete response is shown)
                response_placeholder.markdown(full_response)

                # Add to chat history
                st.session_state.chat_history.append(("assistant", full_response))
                
                # Make sure to set flag to clear uploader on next render
                st.session_state.clear_file_flag = True
                
                # Increment file_uploader_key to force refresh of the uploader component
                if "file_uploader_key" in st.session_state:
                    st.session_state.file_uploader_key += 1

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)
                
                # Make sure to set flag to clear uploader even on error
                st.session_state.clear_file_flag = True
                
                # Increment file_uploader_key to force refresh of the uploader component
                if "file_uploader_key" in st.session_state:
                    st.session_state.file_uploader_key += 1
        # Clean up temp file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

    # =============================================================================
    # Footer
    # =============================================================================
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p><strong>Disclaimer:</strong> Lexi provides general legal information only. 
        This is not legal advice. Consult a qualified lawyer for specific legal matters.</p>
        <p>© 2025 Lexi Law Agent | Powered by LangGraph & Phoenix</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application entry point with authentication."""
    # Initialize session for authentication
    SessionManager.initialize_session()
    
    # Check if user is authenticated and session is valid
    if SessionManager.is_authenticated() and SessionManager.is_session_valid():
        # User is authenticated, load the main application
        load_main_application()
    else:
        # User is not authenticated, show authentication page
        if render_auth_page():
            # Authentication successful, rerun to load main app
            st.rerun()

if __name__ == "__main__":
    main()