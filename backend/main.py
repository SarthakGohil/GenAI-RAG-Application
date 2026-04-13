"""SecureRAG FastAPI: JWT auth, sanitization, upload, Q&A, summarize."""
import json
import langsmith_setup  # noqa: F401
from typing import Annotated

from auth import create_token, verify_token
from config import DEMO_USERS_JSON, LLM_BACKEND
from database import log_query, ping_mongo, create_user, get_user_hash, get_user_history
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from ingest import ingest_pdf_bytes
from pydantic import BaseModel, Field
from rag_pipeline import get_rag_chain, get_summarize_chain
from security import sanitize_input
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="SecureRAG API", version="1.0.0")
oauth2 = OAuth2PasswordBearer(tokenUrl="/login")


class LoginData(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class SummarizeBody(BaseModel):
    focus: str = Field(default="", max_length=500)


def users_map() -> dict[str, str]:
    return json.loads(DEMO_USERS_JSON)


@app.post("/register")
def register(data: LoginData):
    # Check if user already exists
    if get_user_hash(data.username) or data.username in users_map():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password and create
    hashed = pwd_context.hash(data.password)
    success = create_user(data.username, hashed)
    if not success:
        raise HTTPException(status_code=500, detail="Database error during registration")
    
    return {"message": "User registered successfully"}


@app.post("/login")
def login(data: LoginData):
    db_hash = get_user_hash(data.username)
    # Check environmental dummy users as fallback
    if not db_hash:
        users = users_map()
        if data.username in users:
            # Check if it's already a hash or plain text
            stored = users[data.username]
            is_match = False
            try:
                # Try as hash first
                if pwd_context.identify(stored):
                    is_match = pwd_context.verify(data.password, stored)
                else:
                    is_match = (stored == data.password)
            except Exception:
                is_match = (stored == data.password)
            
            if is_match:
                return {"token": create_token(data.username), "token_type": "bearer"}
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not pwd_context.verify(data.password, db_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {"token": create_token(data.username), "token_type": "bearer"}


def current_user(token: Annotated[str, Depends(oauth2)]) -> str:
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@app.post("/upload")
async def upload_pdf(
    user: Annotated[str, Depends(current_user)],
    file: UploadFile = File(...),
):
    name = file.filename or "upload.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    raw = await file.read()
    try:
        n = ingest_pdf_bytes(raw, name, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"chunks_added": n, "filename": name, "user": user}


@app.post("/query")
def query(q: Query, user: Annotated[str, Depends(current_user)]):
    clean = sanitize_input(q.question)
    if not clean.strip():
        raise HTTPException(status_code=400, detail="Empty question after sanitization")
    out = get_rag_chain(user).invoke({"input": clean})
    ans = str(out.get("answer", ""))
    log_query(user, clean, ans)
    return {"answer": ans, "user": user}


@app.post("/summarize")
def summarize(body: SummarizeBody, user: Annotated[str, Depends(current_user)]):
    focus = sanitize_input(body.focus) or "main themes and important facts"
    # Use focus as the input query for retrieval, but keep the instruction for the LLM
    out = get_summarize_chain(user).invoke({"input": focus})
    ans = str(out.get("answer", ""))
    log_query(user, "SUMMARIZE:" + focus[:200], ans)
    return {"summary": ans, "user": user}
@app.get("/history")
def get_history(user: Annotated[str, Depends(current_user)]):
    history = get_user_history(user)
    return {"history": history, "user": user}

@app.get("/health")
def health():
    return {"status": "ok", "mongo": ping_mongo(), "llm_backend": LLM_BACKEND}
