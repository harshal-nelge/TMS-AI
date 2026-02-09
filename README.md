# TMS AI Document Processing System

**AI-powered logistics document processing and question answering system for Transportation Management Systems**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)](https://streamlit.io)

## 🎯 Overview

TMS AI is a POC system that enables users to upload logistics documents (PDFs, DOCX, TXT) and interact with them using natural language questions. The system uses Retrieval-Augmented Generation (RAG) to provide grounded answers with confidence scores, applies guardrails to prevent hallucinations, and can extract structured shipment data.

### Key Features

- 📄 **Document Upload & Processing**: Support for PDF, DOCX, and TXT logistics documents
- 💬 **Natural Language Q&A**: Ask questions and get context-grounded answers with source citations
- 📊 **Structured Data Extraction**: Extract shipment information into JSON format
- 🛡️ **Guardrails**: Confidence thresholds prevent low-quality answers
- 🔄 **Retry Mechanism**: Exponential backoff for API rate limits
- 🎨 **Modern UI**: Clean Streamlit interface for easy interaction

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                       │
│          (Upload │ Q&A Interface │ Extraction View)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  POST /upload │ POST /ask │ POST /extract │ DELETE /document│
└────────┬─────────────────┬──────────────────┬───────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌────────────────┐
│   Document      │  │  RAG Engine  │  │   Extractor    │
│   Processor     │  │              │  │                │
│  - PDF Parse    │  │ - Retrieval  │  │ - Structured   │
│  - Chunking     │  │ - LLM Gen    │  │   Extraction   │
│  - Metadata     │  │ - Scoring    │  │ - JSON Schema  │
└────────┬────────┘  └──────┬───────┘  └────────┬───────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Vector Store Manager (ChromaDB)                 │
│  - Mistral Embeddings │ Similarity Search │ Persistence     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload**: Document → Parse → Chunk → Embed → Store in ChromaDB
2. **Question**: Query → Retrieve top-k chunks → LLM generates answer → Score confidence → Apply guardrails
3. **Extract**: Retrieve document chunks → LLM extracts fields → Validate JSON → Return structured data

## 🧠 Technical Approach

### Chunking Strategy

- **Method**: RecursiveCharacterTextSplitter
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Separators**: Prioritizes paragraphs (`\n\n`), lines (`\n`), sentences (`. `), then words
- **Metadata**: Each chunk includes document ID, filename, chunk index, and total chunks

**Rationale**: This approach preserves document structure while ensuring semantic completeness. The overlap prevents information loss at chunk boundaries, critical for logistics documents where context matters.

### Retrieval Method

- **Vector Database**: ChromaDB with persistent storage
- **Embeddings**: Mistral Embed (`mistral-embed` model)
- **Retrieval**: Similarity search with top-k=3 chunks
- **Scoring**: L2 distance converted to similarity scores (1 - normalized_distance)

**Rationale**: ChromaDB provides efficient local vector storage. Top-k=3 balances context richness with LLM token limits. Mistral embeddings are cost-effective and performant for domain-specific text.

### Guardrails Approach

1. **Similarity Threshold**: Minimum 0.5 average retrieval score required
2. **Confidence Threshold**: Answers below 0.5 confidence trigger refusal
3. **Grounding Instructions**: LLM explicitly instructed to answer only from context
4. **Source Citation**: All answers include source chunks for verification

**Rationale**: Multi-layer guardrails prevent hallucinations. The 0.5 threshold was chosen to balance recall (answering valid questions) with precision (avoiding low-confidence responses).

### Confidence Scoring Method

**Formula**: `Confidence = (0.7 × Retrieval Similarity) + (0.3 × Source Agreement)`

- **Retrieval Similarity**: Average similarity score from top-k chunks
- **Source Agreement**: 1.0 if multiple sources available, 0.7 otherwise
- **Categories**: High (≥0.7), Medium (0.5-0.7), Low (<0.5)

**Rationale**: Weights retrieval quality heavily (70%) as it's the primary signal, while source agreement (30%) adds confidence when multiple chunks support the answer.

### Retry Mechanism

- **Library**: `tenacity` with exponential backoff
- **Max Retries**: 3 attempts
- **Backoff**: 1s → 2s → 4s → 8s (max 10s)
- **Retry Conditions**: Rate limits (429), token limits, service errors (503)
- **Applied To**: All LLM calls (Groq) and embedding calls (Mistral)

**Rationale**: Protects against transient API failures and rate limits without overwhelming the services.

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- API Keys for:
  - Groq (for LLM)
  - Mistral AI (for embeddings)

### Local Setup

1. **Clone and navigate to directory**
```bash
cd "/Users/harshalnelge/Desktop/TMS AI"
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

The `.env` file already contains:
```env
MISTRAL_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

5. **Run the FastAPI server**
```bash
uvicorn app:app --reload --port 8000
```

6. **Run the Streamlit UI** (in a new terminal)
```bash
streamlit run ui/streamlit_app.py --server.port 8501
```

7. **Access the application**
- API Documentation: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

## 📖 Usage Guide

### Via Streamlit UI

1. **Upload Document** → Navigate to "Upload Document" tab → Choose file → Click "Process Document"
2. **Ask Questions** → Go to "Ask Questions" tab → Enter question → View answer with confidence and sources
3. **Extract Data** → Go to "Extract Data" tab → Click "Extract Data" → Download JSON

### Via API

**Upload Document:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@path/to/document.pdf"
```

**Ask Question:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-document-id",
    "question": "What is the carrier rate?"
  }'
```

**Extract Structured Data:**
```bash
curl -X POST "http://localhost:8000/extract?document_id=your-document-id"
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/upload` | POST | Upload and process document |
| `/ask` | POST | Ask question about document |
| `/extract` | POST | Extract structured shipment data |
| `/document/{id}` | DELETE | Delete document and vector store |

Full API documentation available at http://localhost:8000/docs when server is running.

## ⚠️ Known Failure Cases

1. **Scanned PDFs**: Text extraction fails on image-based PDFs (requires OCR)
2. **Complex Tables**: Table structure may be lost during chunking
3. **Multi-Document References**: Cannot answer questions spanning multiple uploaded documents
4. **Ambiguous Questions**: Vague questions may trigger guardrails even with relevant content
5. **Large Documents**: Very large files (>10MB) are rejected due to size limits
6. **Missing Fields**: Extraction returns null for fields not present in document

## 💡 Future Improvements

1. **OCR Integration**: Add Tesseract/Azure Form Recognizer for scanned documents
2. **Table Extraction**: Specialized chunking for tabular data
3. **Multi-Document RAG**: Query across multiple uploaded documents
4. **Streaming Responses**: Real-time answer generation for better UX
5. **Fine-tuned Embeddings**: Domain-specific embedding model for logistics
6. **Citation Precision**: Line-level source highlighting in UI
7. **Batch Processing**: Upload and process multiple documents simultaneously
8. **Persistent Storage**: Database backend instead of in-memory registry
9. **User Authentication**: Multi-user support with document isolation
10. **Advanced Analytics**: Track question patterns and confidence trends

## 🛠️ Tech Stack

- **Backend**: FastAPI 0.109.0
- **UI**: Streamlit 1.31.0
- **LLM**: ChatGroq (llama-3.1-8b-instant)
- **Embeddings**: Mistral Embed
- **Vector DB**: ChromaDB 0.4.22
- **Document Processing**: LangChain, PyPDF, python-docx
- **Retry Logic**: Tenacity 8.2.3

## 📁 Project Structure

```
TMS AI/
├── app.py                      # FastAPI application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .gitignore                 # Git ignore patterns
├── config/
│   └── settings.py            # Configuration management
├── models/
│   └── schemas.py             # Pydantic data models
├── modules/
│   ├── document_processor.py # Document parsing and chunking
│   ├── vector_store.py        # ChromaDB vector management
│   ├── rag_engine.py          # RAG Q&A with guardrails
│   └── extractor.py           # Structured data extraction
├── utils/
│   ├── helpers.py             # Utility functions
│   └── retry_utils.py         # Retry mechanisms
├── ui/
│   └── streamlit_app.py       # Streamlit user interface
├── uploads/                   # Uploaded documents (gitignored)
├── chroma_db/                 # Vector database (gitignored)
└── docs/
    └── ARCHITECTURE.md        # Detailed architecture docs
```

## 📝 License

This is a POC project created for demonstration purposes.

## 👤 Author

Built with ❤️ for TMS AI Assignment

---

**Questions or Issues?** Check the API docs at `/docs` or review the logs for debugging.
