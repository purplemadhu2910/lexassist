from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
from ai_engine import AIEngine
from document_parser import DocumentParser
from database import Database
import logging
import os
import pickle
import secrets
import threading
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LexAssist API",
    description="AI-powered legal and tax assistant backend",
    version="1.0.0"
)

# Fix 3: CORS — allow localhost for dev, and the Render public URL for prod
_frontend_url = os.getenv("FRONTEND_URL", "")
ALLOWED_ORIGINS = ["http://localhost:8501", "http://127.0.0.1:8501"]
if _frontend_url:
    ALLOWED_ORIGINS += [u.strip() for u in _frontend_url.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ai_engine = AIEngine()
doc_parser = DocumentParser()
db = Database()

# Fix 1: Simple in-memory rate limiter for login attempts
_login_attempts: dict = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 60  # seconds

def check_rate_limit(ip: str):
    now = time.time()
    attempts = _login_attempts[ip]
    # Remove attempts outside the window
    _login_attempts[ip] = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    if len(_login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in a minute.")
    _login_attempts[ip].append(now)

# Fix 4+5: File-backed token store with file locking to prevent corruption
_SESSIONS_FILE = "/tmp/lexassist_sessions.pkl"
_sessions_lock = threading.Lock()

def _load_sessions() -> dict:
    if os.path.exists(_SESSIONS_FILE):
        try:
            with open(_SESSIONS_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            return {}
    return {}

def _save_sessions(sessions: dict):
    tmp = _SESSIONS_FILE + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(sessions, f)
    os.replace(tmp, _SESSIONS_FILE)  # atomic write

def create_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    with _sessions_lock:
        sessions = _load_sessions()
        sessions[token] = user_id
        _save_sessions(sessions)
    return token

def get_current_user(request: Request) -> int:
    token = request.headers.get("X-Auth-Token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with _sessions_lock:
        sessions = _load_sessions()
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[token]

# Fix 2: Input sanitization
BLOCKED_PATTERNS = ["ignore previous", "disregard", "you are now", "new instructions", "system prompt"]

def sanitize_query(query: str) -> str:
    lower = query.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            raise HTTPException(status_code=400, detail="Invalid query content.")
    return query.strip()[:2000]  # cap length


class QueryRequest(BaseModel):
    query: str
    category: str = "general"

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v not in ("legal", "tax", "general", "document"):
            return "general"
        return v

class QueryResponse(BaseModel):
    response: str
    category: str
    suggested_questions: list[str] = []

class AuthRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        v = v.strip()
        if not v or len(v) > 50:
            raise ValueError("Invalid username")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) > 128:
            raise ValueError("Invalid password")
        return v


@app.get("/")
async def root():
    return {"message": "Welcome to LexAssist API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    try:
        stats = db.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "total_queries": stats["total_queries"],
            "queries_by_category": stats["by_category"]
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@app.post("/register")
async def register(request: AuthRequest):
    success = db.register_user(request.username, request.password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Account created successfully"}

@app.post("/login")
async def login(request: AuthRequest, req: Request):
    # Fix 1: Rate limit by IP
    client_ip = req.client.host
    check_rate_limit(client_ip)

    user = db.login_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(user["id"])
    return {"message": "Login successful", "token": token, "user_id": user["id"], "username": user["username"]}

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest, user_id: int = Depends(get_current_user)):
    try:
        # Fix 2: Sanitize input
        query = sanitize_query(request.query)

        logger.info(f"Processing query: {query[:50]}...")
        response = await ai_engine.process_query(query, request.category)
        db.save_query(query, response, request.category, user_id)
        suggestions = ai_engine.generate_suggestions(query, request.category)

        return QueryResponse(
            response=response,
            category=request.category,
            suggested_questions=suggestions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing query")

@app.post("/explain-document")
async def explain_document(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        allowed_extensions = ['.pdf', '.txt']
        file_ext = '.' + file.filename.split('.')[-1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

        extracted_text = doc_parser.extract_text(content, file_ext)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from document")

        explanation = await ai_engine.explain_document(extracted_text)

        return {
            "filename": file.filename,
            "extracted_text": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
            "explanation": explanation,
            "text_length": len(extracted_text)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing document")

# Fix 4: /history now requires authentication, only returns own history
@app.get("/history")
async def get_history(limit: int = 50, user_id: int = Depends(get_current_user)):
    try:
        history = db.get_history(limit, user_id)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching history")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
