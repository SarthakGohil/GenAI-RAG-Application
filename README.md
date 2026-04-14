# SecureRAG

A simple tool to chat with your PDFs. Upload documents, ask questions, and get answers.

### What it does:
- Upload up to 5 PDFs
- Ask questions about your documents
- Get summaries with specific focus
- Secure user accounts with login
- All data stored in MongoDB Atlas

---

## How to Use

### 1. Backend (Hugging Face Spaces)
- Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
- Choose Docker → Blank
- Upload files from `spaces/backend/`
- Add these secrets in Space settings:
  - `MONGODB_URI` — Your MongoDB connection string
  - `MONGODB_DB` — securerag
  - `GROQ_API_KEY` — Your Groq API key
  - `HF_TOKEN` — Your HuggingFace token
  - `JWT_SECRET` — Any random string
  - `LLM_BACKEND` — groq
- Update `main.py` line 19 with your Streamlit URL (for CORS)

### 2. Frontend (Streamlit Cloud)
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub repo
- Select `frontend/app.py`
- Add secret: `API_URL` = your HF backend URL

### 3. MongoDB Atlas
- Go to Network Access
- Add IP: Allow from Anywhere

---

## Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## Tech Used
- FastAPI, Streamlit, LangChain
- MongoDB Atlas, Groq LLM
- HuggingFace Spaces, Streamlit Cloud