# SecureRAG Frontend

## How to Deploy

### 1. Deploy Backend First
Follow instructions in `spaces/README.md` to deploy backend on HF Spaces.

### 2. Create App
- Go to [share.streamlit.io](https://share.streamlit.io)
- Sign in with GitHub
- Click **New app**
- Select repo: `SarthakGohil/GenAI-RAG-Application`
- Branch: `main`
- Main file: `frontend/app.py`

### 3. Add Secret
In app settings add:
- Key: `API_URL`
- Value: `https://your-hf-space-name.hf.space`

---

## Notes
- Frontend runs on Streamlit Cloud (free)
- Backend on HF Spaces (16GB RAM, free)
- MongoDB Atlas for persistent storage