# SecureRAG - Hugging Face Spaces Backend

## Deployment Instructions

### 1. Create a New Hugging Face Space
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Docker** → **Blank** as the SDK
3. Give your Space a name (e.g., `securerag-backend`)
4. Set visibility to **Public** or **Private** as needed
5. Click **Create Space**

### 2. Upload Your Files
Upload the contents of this folder (`spaces/backend/`) to your new HF Space:
- `main.py`
- `auth.py`
- `config.py`
- `database.py`
- `ingest.py`
- `langsmith_setup.py`
- `llm_factory.py`
- `rag_pipeline.py`
- `security.py`
- `requirements.txt`
- `Dockerfile`

### 3. Add Your Secrets (Environment Variables)
In your HF Space settings, add these secrets:

| Name | Value |
|------|-------|
| `MONGODB_URI` | Your MongoDB Atlas connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net`) |
| `MONGODB_DB` | `securerag` (or your preferred database name) |
| `GROQ_API_KEY` | Your Groq API key |
| `HF_TOKEN` | Your HuggingFace API token (for embeddings) |
| `JWT_SECRET` | A long random string for JWT signing |
| `LLM_BACKEND` | `groq` |

### 4. MongoDB Atlas Network Access
If your MongoDB Atlas is locked to specific IPs:
1. Go to **MongoDB Atlas** → **Security** → **Network Access**
2. Click **Add IP Address**
3. Select **Allow Access from Anywhere** (0.0.0.0/0)
4. Confirm

### 5. Update Your Frontend
In your Render/Vercel frontend settings, update the `API_URL` environment variable:
```
API_URL=https://your-hf-space-name.hf.space
```

### 6. Architecture Summary
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  HF Spaces       │────▶│  MongoDB Atlas  │
│   (Render/      │     │  Backend         │     │  (Cloud DB)     │
│    Vercel)      │◀────│  (16GB RAM!)     │◀────│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Why Hugging Face Spaces?
- **16GB RAM** (vs Render's 512MB) - No more memory freezes!
- **Persistent storage** via MongoDB Atlas - Data survives Space restarts
- **Free forever** on Starter tier - No credit card needed