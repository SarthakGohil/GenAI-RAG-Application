# SecureRAG Frontend - Streamlit Community Cloud Deployment

## Deployment Steps

### 1. Create a New Space on Hugging Face
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Streamlit** as the SDK
3. Name it `securerag-frontend` (or your choice)
4. Set visibility to **Public**
5. Click **Create Space**

### 2. Upload Your Files
Upload all files from this folder (`frontend/`):
- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`

**Important:** Do NOT upload `secrets.toml` or any file containing actual API keys/secrets!

### 3. Add Your API_URL Secret
In your HF Space settings:
1. Go to **Settings** → **Variables and secrets**
2. Click **New secret**
3. Name: `API_URL`
4. Value: Your HuggingFace backend URL (e.g., `https://apun-007-securerag-backend.hf.space`)
5. Click **Add secret**

### 4. Wait for Deployment
Streamlit Community Cloud will automatically build and deploy your app.

Your frontend will be live at: `https://apun-007-securerag-frontend.hf.space`

---

## Architecture After Deployment
```
User Browser
    │
    ▼
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│  Streamlit Community    │────▶│  HuggingFace Spaces     │────▶│  MongoDB Atlas  │
│  Cloud (Frontend)       │     │  Backend (16GB RAM!)    │     │  (Cloud DB)     │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────┘
```

## Notes
- Frontend is free on Streamlit Community Cloud
- Backend is on HuggingFace Spaces (16GB RAM, never freezes!)
- MongoDB Atlas is your persistent cloud database