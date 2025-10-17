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

**Tech Stack**: LangGraph • Streamlit • Azure Blob • Azure Postgres • OpenAI GPT • Redis Cloud • Azure Devops

---

## 🏗️ Architecture

### High-Level System Flow

<img width="2801" height="4565" alt="lexi-flow-diagram" src="https://github.com/user-attachments/assets/98920185-ca33-4f7d-96b9-77a6c3767789" />


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

## 🚀 Deployment

### Option 1: Local Setup

```bash
# Clone repository
git clone https://github.com/Rajatsharma786/lexi_lawagent.git
cd lexi_lawagent

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run application
streamlit run src/app.py
```

### Option 2: Docker Deployment 🐳

**Quick Start**:
```bash
# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Build and run
docker-compose up -d

# Access at http://localhost:8501
```

**Manual Docker Build**:
```bash
docker build -t lexi-law-agent .
docker run -p 8501:8501 --env-file .env lexi-law-agent
```

See [DOCKER.md](DOCKER.md) for detailed deployment instructions.

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

### Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test_file.py -v

# Run quick tests only
pytest test_file.py -v -m "not integration and not performance"

# Run with coverage report
pytest test_file.py --cov=src --cov-report=html

# Use test runner scripts
# Windows:
run-tests.bat

# Linux/Mac:
./run-tests.sh
```

**Test Coverage**:
- ✅ Repository structure & imports
- ✅ Authentication & security
- ✅ Agent system functionality  
- ✅ Redis caching & Azure Blob sync
- ✅ Docker configuration

---
