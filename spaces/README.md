# SecureRAG Backend

## How to Deploy

### 1. Create Space
- Go to [huggingface.co/new-space](https://huggingface.co/new-space)
- Select **Docker** → **Blank**
- Name: `securerag-backend`
- Visibility: **Public**

### 2. Upload Files
Upload these files from `spaces/backend/`:
- main.py, auth.py, config.py, database.py, ingest.py
- langsmith_setup.py, llm_factory.py, rag_pipeline.py
- security.py, requirements.txt, Dockerfile

### 3. Add Secrets
In Space settings add these:

| Name | Value |
|------|-------|
| MONGODB_URI | Your MongoDB connection string |
| MONGODB_DB | securerag |
| GROQ_API_KEY | Your Groq API key |
| HF_TOKEN | Your HuggingFace token |
| JWT_SECRET | Any random string |
| LLM_BACKEND | groq |

### 4. MongoDB Atlas
- Go to **Security** → **Network Access**
- Click **Add IP Address**
- Select **Allow Access from Anywhere**

### 5. Update main.py
Before uploading, edit line 16 in main.py:
```python
"https://genai-rag-application.streamlit.app"  # replace with your streamlit url
```

---

## Architecture
```
Streamlit Cloud ──▶ HF Spaces Backend ──▶ MongoDB Atlas
```

## Why HF Spaces?
- 16GB RAM (free)
- No memory freezes
- Persistent via MongoDB