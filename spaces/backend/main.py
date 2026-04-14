"""SecureRAG FastAPI: JWT auth, sanitization, upload, Q&A, summarize."""
import json
import os
import uvicorn
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

# Lazy loading is used within endpoints to ensure fast startup on Render free tier

app = FastAPI(title="SecureRAG API", version="1.0.0")
oauth2 = OAuth2PasswordBearer(tokenUrl="/login")

@app.get("/ping")
def ping():
    """Ultra-lightweight endpoint for UptimeRobot/Keep-alive."""
    return {"status": "alive"}

def get_pwd_context():
    from passlib.context import CryptContext
    return CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginData(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class SummarizeBody(BaseModel):
    focus: str = Field(default="", max_length=500)


def users_map() -> dict[str, str]:
    from config import DEMO_USERS_JSON
    return json.loads(DEMO_USERS_JSON)


@app.post("/register")
def register(data: LoginData):
    from database import get_user_hash, create_user
    # Check if user already exists
    if get_user_hash(data.username) or data.username in users_map():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password and create
    pwd_context = get_pwd_context()
    hashed = pwd_context.hash(data.password)
    success = create_user(data.username, hashed)
    if not success:
        raise HTTPException(status_code=500, detail="Database error during registration")
    
    return {"message": "User registered successfully"}


@app.post("/login")
def login(data: LoginData):
    from database import get_user_hash
    from auth import create_token
    db_hash = get_user_hash(data.username)
    # Check environmental dummy users as fallback
    if not db_hash:
        users = users_map()
        if data.username in users:
            # Check if it's already a hash or plain text
            stored = users[data.username]
            is_match = False
            pwd_context = get_pwd_context()
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
        
    pwd_context = get_pwd_context()
    if not pwd_context.verify(data.password, db_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {"token": create_token(data.username), "token_type": "bearer"}


def current_user(token: Annotated[str, Depends(oauth2)]) -> str:
    from auth import verify_token
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
    
    from ingest import ingest_pdf_bytes
    raw = await file.read()
    try:
        n = ingest_pdf_bytes(raw, name, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"chunks_added": n, "filename": name, "user": user}


@app.post("/query")
def query(q: Query, user: Annotated[str, Depends(current_user)]):
    import langsmith_setup  # noqa: F401
    from rag_pipeline import get_rag_chain
    from security import sanitize_input
    from database import log_query
    clean = sanitize_input(q.question)
    if not clean.strip():
        raise HTTPException(status_code=400, detail="Empty question after sanitization")
    out = get_rag_chain(user).invoke({"input": clean})
    ans = str(out.get("answer", ""))
    log_query(user, clean, ans)
    return {"answer": ans, "user": user}


@app.post("/summarize")
def summarize(body: SummarizeBody, user: Annotated[str, Depends(current_user)]):
    import langsmith_setup  # noqa: F401
    from rag_pipeline import get_summarize_chain
    from security import sanitize_input
    from database import log_query
    focus = sanitize_input(body.focus) or "main themes and important facts"
    # Use focus as the input query for retrieval, but keep the instruction for the LLM
    out = get_summarize_chain(user).invoke({"input": focus})
    ans = str(out.get("answer", ""))
    log_query(user, "SUMMARIZE:" + focus[:200], ans)
    return {"summary": ans, "user": user}
@app.get("/history")
def get_history(user: Annotated[str, Depends(current_user)]):
    from database import get_user_history
    history = get_user_history(user)
    return {"history": history, "user": user}

@app.get("/health")
def health():
    from database import ping_mongo
    from config import LLM_BACKEND
    return {"status": "ok", "mongo": ping_mongo(), "llm_backend": LLM_BACKEND}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
