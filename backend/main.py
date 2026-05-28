from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from ai_engine import AIEngine
from document_parser import DocumentParser
from database import Database
import logging
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LexAssist API",
    description="AI-powered legal and tax assistant backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_engine = AIEngine()
doc_parser = DocumentParser()
db = Database()

class QueryRequest(BaseModel):
    query: str
    category: str = "general"
    user_id: Optional[int] = None

class QueryResponse(BaseModel):
    response: str
    category: str
    suggested_questions: list[str] = []

class AuthRequest(BaseModel):
    username: str
    password: str

@app.get("/")
async def root():
    return {
        "message": "Welcome to LexAssist API",
        "version": "1.0.0",
        "endpoints": ["/ask", "/explain-document", "/health", "/login", "/register"]
    }

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
    if not request.username.strip() or not request.password.strip():
        raise HTTPException(status_code=400, detail="Username and password cannot be empty")
    success = db.register_user(request.username.strip(), request.password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Account created successfully"}

@app.post("/login")
async def login(request: AuthRequest):
    user = db.login_user(request.username.strip(), request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful", "user_id": user["id"], "username": user["username"]}

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        logger.info(f"Processing query: {request.query[:50]}...")

        response = await ai_engine.process_query(request.query, request.category)
        db.save_query(request.query, response, request.category, request.user_id)
        suggestions = ai_engine.generate_suggestions(request.query, request.category)

        return QueryResponse(
            response=response,
            category=request.category,
            suggested_questions=suggestions
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/explain-document")
async def explain_document(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        allowed_extensions = ['.pdf', '.txt']
        file_ext = '.' + file.filename.split('.')[-1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        logger.info(f"Processing document: {file.filename}")

        content = await file.read()
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
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/history")
async def get_history(limit: int = 50, user_id: int = None):
    try:
        history = db.get_history(limit, int(user_id) if user_id is not None else None)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
