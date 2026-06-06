# ⚖️ LexAssist — AI Legal & Tax Assistant for Indian Law

LexAssist is an AI-powered legal and tax assistant that helps users understand complex Indian legal and tax concepts in simple, easy-to-understand language. It uses Retrieval-Augmented Generation (RAG) to ground answers in real Indian legal documents.

---

## 🚀 Features

- **Legal Question Assistant** — Ask anything about IPC, Constitution, CRPC in plain language
- **Tax Assistant** — Understand Income Tax, GST, deductions without the jargon
- **Document Analysis** — Upload any legal PDF or TXT and get a plain-language explanation
- **RAG-Enhanced Answers** — Responses grounded in real Indian legal documents via FAISS vector search
- **User Authentication** — Register and login with bcrypt-hashed passwords
- **Query History** — View and filter all your past queries per user
- **Suggested Follow-up Questions** — AI-generated follow-up questions after every response

---

## 🧠 Knowledge Base

| Document | Type | Approximate Size |
|---|---|---|
| Indian Penal Code (IPC) Q&A | JSON | ~10,000 pairs |
| Constitution of India Q&A | JSON | ~5,000 pairs |
| CRPC (Code of Criminal Procedure) Q&A | JSON | ~3,000 pairs |
| IndicLegalQA Dataset | JSON | 10,000 Q&A pairs |
| Income Tax Bill 2025 | PDF | ~200 pages |
| Legal Contract Clauses | CSV | ~500 rows |
| Various legal PDFs (schedules, agreements, case documents) | PDF | ~9 files |
| Domain-specific text files (GST, rent, business, tax, startup, contracts) | TXT | 6 files |
| **Total** | | **~50 MB** |

---

## 🛠️ Tech Stack

### Backend
| Component | Technology |
|---|---|
| API Framework | FastAPI |
| Server | Uvicorn (ASGI) |
| Data Validation | Pydantic v2 |
| Authentication | bcrypt |
| Database | SQLite |
| Environment Variables | python-dotenv |
| PDF Parsing | PyPDF2, pdfplumber |
| File Upload | python-multipart |

### Frontend
| Component | Technology |
|---|---|
| UI Framework | Streamlit |
| HTTP Client | requests |

### AI / LLM
| Component | Technology |
|---|---|
| Language Model | Groq API — LLaMA 3.1 8B Instant |
| LLM Task | Legal Q&A, document explanation, follow-up suggestions |

### RAG Pipeline
| Component | Technology |
|---|---|
| Vector Store | FAISS (faiss-cpu) |
| Text Embeddings | Sentence-Transformers (all-MiniLM-L6-v2) |
| Embedding Framework | PyTorch |
| Tokenizers | Hugging Face Transformers |
| Similarity Search | L2 distance, top-3 chunk retrieval |

### Data Ingestion
| Component | Technology |
|---|---|
| PDF Extraction | pdfplumber |
| JSON Processing | Python built-in json |
| CSV/Excel Processing | pandas, openpyxl |
| Text Chunking | Custom sliding window (1000 chars, 200 overlap) |

### ML / Data Libraries
| Library | Usage |
|---|---|
| NumPy | Embedding array operations |
| scikit-learn | Supporting ML utilities |
| pandas | Tabular data processing |

---

## 🏗️ Architecture

```
User (Browser)
     │
     ▼
Streamlit Frontend (port 8501)
     │  HTTP requests
     ▼
FastAPI Backend (port 8000)
     │
     ├──► RAG Engine
     │         │
     │         ├──► FAISS Vector Store (index.faiss)
     │         │         └── Sentence-Transformers (all-MiniLM-L6-v2)
     │         └──► Returns top-3 relevant chunks
     │
     ├──► Groq API (LLaMA 3.1 8B)
     │         └── Generates response using retrieved context
     │
     └──► SQLite Database
               ├── users table (auth)
               └── query_history table
```

---

## 📁 Project Structure

```
combined/
├── backend/
│   ├── main.py              # FastAPI app & API routes
│   ├── ai_engine.py         # Groq LLM integration & prompt building
│   ├── rag_engine.py        # FAISS vector search & context builder
│   ├── build_index.py       # Builds the FAISS vector index
│   ├── database.py          # SQLite user auth & query history
│   └── document_parser.py   # PDF & TXT text extraction
├── frontend/
│   └── app.py               # Streamlit UI (login, Q&A, history, docs)
├── ingestion/
│   ├── load_pdfs.py         # Extract text from PDFs using pdfplumber
│   ├── load_json.py         # Extract text from JSON datasets
│   ├── load_excel.py        # Extract text from CSV/Excel files
│   └── chunk_text.py        # Split cleaned text into overlapping chunks
├── data/
│   ├── raw/                 # Original source files (PDF, JSON, CSV, TXT)
│   └── processed/           # Cleaned text & chunks (auto-generated)
├── build.py                 # Unified build script for deployment
├── render.yaml              # Render deployment configuration
├── runtime.txt              # Python version for Render (3.11.9)
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── start.bat                # Windows one-click startup script
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/purplemadhu2910/lexassist.git
cd lexassist
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
copy .env.example .env
```
Open `.env` and add your Groq API key:
```
GROQ_API_KEY=your-groq-api-key-here
```

### 4. Run data ingestion (first time only)
```bash
cd ingestion
python load_pdfs.py
python load_json.py
python load_excel.py
python chunk_text.py
```

### 5. Build the vector index (first time only)
```bash
cd backend
python build_index.py
```
This generates the FAISS index from all processed documents. Takes a few minutes.

---

## ▶️ Running the App

### Option 1 — One click (Windows)
Double-click `start.bat` in the `combined` folder.

### Option 2 — Manual (two terminals)

**Terminal 1 — Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
streamlit run app.py
```

### Access
| Service | URL |
|---|---|
| Frontend UI | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 🌐 Deployment (Render)

### Backend
1. Go to [render.com](https://render.com) → New Web Service
2. Connect your GitHub repo
3. Set:
   - Root Directory: `.` (project root)
   - Build Command: `pip install -r requirements.txt && python build.py`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `GROQ_API_KEY` = your Groq API key
   - `PYTHON_VERSION` = `3.11.9`

### Frontend
1. New Web Service → same repo
2. Set:
   - Root Directory: `.` (project root)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd frontend && streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
3. Add environment variables:
   - `API_URL` = your backend Render URL (e.g. `https://lexassist-backend.onrender.com`)
   - `PYTHON_VERSION` = `3.11.9`

---

## 🔒 Security Notes

- Never commit your `.env` file — it is listed in `.gitignore`
- Passwords are hashed using `bcrypt` before storing in the database
- CORS is configured with `allow_credentials=False` for security
- This app is for informational purposes only and does not store sensitive personal data

---

## ⚠️ Disclaimer

LexAssist is an AI-powered informational tool only. Responses are generated by an AI model and are **not legal or tax advice**. Always consult a qualified lawyer or tax professional for specific guidance.

---

## 👨‍💻 Author

Built as a Final Year Project (FYP) — AI-powered legal assistance for Indian law using RAG.

- GitHub: [purplemadhu2910](https://github.com/purplemadhu2910)
