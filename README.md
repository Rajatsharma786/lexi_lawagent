# 🏛️ Lexi Law Agent

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://langchain-ai.github.io/langgraph/)
[![Azure](https://img.shields.io/badge/Azure-Cloud-0089D6.svg)](https://azure.microsoft.com/)

An intelligent multi-agent legal assistant specialized in Victorian (Australia) legislation, statutory rules, and court procedures. Built with LangGraph, featuring document analysis, form generation, and cloud-native architecture.

---

## 🎯 Overview

Lexi is a production-ready AI legal assistant that helps users:
- 🔍 Understand Victorian Acts, regulations, and statutory rules
- 📋 Generate court forms for Magistrate, Supreme, and Federal courts
- 📄 Analyze legal documents (PDFs, images) using OCR
- 💬 Get instant answers with intelligent agent routing

**Tech Stack**: LangGraph • Streamlit • ChromaDB • OpenAI GPT • Redis Cloud • Azure

---

## 🏗️ Architecture

### High-Level System Flow

```
User → Authentication (Azure PostgreSQL) → Streamlit UI
                                              │
                                      Supervisor Agent
                                              │
                        ┌─────────────────────┼────────────────┐
                        ▼                     ▼                ▼
                   Law Agent          Procedure Agent    General Agent
                        │                     │
                  ┌─────┴─────┐         ┌─────┴─────┐
                  │           │         │           │
            Redis Cache   ChromaDB  Redis Cache  ChromaDB
                  │       (local)       │       (local)
                  │    (synced from     │    (synced from
                  │    Azure Blob)      │    Azure Blob)
                  │                     │
                  └──────────┬──────────┘
                             ▼
                      LLM Response → UI
```

### Key Components

- **Authentication**: Fast-loading auth with Azure PostgreSQL
- **Multi-Agent System**: Supervisor routes to specialized agents (Law, Procedure, General)
- **Vector Storage**: ChromaDB synced from Azure Blob Storage to local cache
- **Caching Layer**: Redis Cloud for query-level caching (~60% faster repeat queries)
- **Observability**: Phoenix/Arize for real-time tracing

---

##  Key Features

-  **Fast Authentication**: Lazy-loading architecture with Azure PostgreSQL
-  **Multi-Agent Routing**: Supervisor intelligently routes to Law, Procedure, or General agents
-  **Document Analysis**: OCR extraction from PDFs and images (Tesseract, docTR, PDF Plumber)
-  **Court Form Generation**: Dynamic PDF creation for Victorian courts
-  **Cloud-Native**: Azure Blob Storage (ChromaDB sync) + Redis Cloud (caching)
-  **Professional UI**: Clean Streamlit interface with markdown rendering


---

## How It Works

### 1. Data Collection
Scrape Victorian legislation PDFs from [legislation.vic.gov.au](https://www.legislation.vic.gov.au) using keyword-based filtering.

### 2. Data Processing
- Load PDFs and clean text
- Chunk documents (1000 chars, 200 overlap)
- Generate embeddings using Legal BERT
- Store in ChromaDB collections

### 3. Agent Routing
```
User Query → Supervisor → [Law Agent | Procedure Agent | General Agent]
```

- **Law Agent**: Interprets legislation, provides statutory analysis
- **Procedure Agent**: Court procedures, generates forms
- **General Agent**: Casual legal Q&A

### 4. Retrieval & Response
1. Check Redis Cloud cache
2. If miss → Query ChromaDB (local, synced from Azure Blob)
3. Rerank results with CrossEncoder
4. Generate LLM response
5. Cache in Redis (1hr TTL)

---

## Usage Examples

**Legislative Query**:
```
"What are the workplace safety requirements under the OHS Act?"
```

**Court Procedure**:
```
"How do I file an appeal in Magistrate Court? Generate the form."
```

**Document Analysis**:
```
[Upload summons.pdf]
"Analyze this summons and tell me the hearing date"
```

---

## Cloud Services

### Azure PostgreSQL
- User authentication and session management
- Auto-creates `users` table on first run

### Azure Blob Storage
- Hosts ChromaDB collections (read-only source)
- One-way sync to local `.chroma_cache/`
- Requires SAS URLs with read+list permissions

### Redis Cloud
- Query-level caching (1hr TTL)
- ~60% reduction in ChromaDB lookups
- Managed Redis instance

### Phoenix/Arize
- Real-time agent tracing and observability
- Token usage and latency metrics

---

## Development

### Adding New Agents

1. Define agent node in `agentsandnodes.py`
2. Update supervisor routing logic
3. Add node to graph in `agent_flow_calling.py`

### Adding New Tools

1. Define tool in `tools.py` with `@tool` decorator
2. Bind tool to agent in `agentsandnodes.py`

# Test Streamlit UI
streamlit run src/app.py

---

## 🙏 Acknowledgments

- **Victorian Legislation**: [legislation.vic.gov.au](https://www.legislation.vic.gov.au)
- **LangChain/LangGraph**: Multi-agent framework
- **Arize Phoenix**: Observability platform
- **Legal BERT**: [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

---

## 📧 Contact

**GitHub**: [@Rajatsharma786](https://github.com/Rajatsharma786)  
**Repository**: [lexi_lawagent](https://github.com/Rajatsharma786/lexi_lawagent)

---
