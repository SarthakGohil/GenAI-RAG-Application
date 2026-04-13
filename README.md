# SecureRAG

A simple tool to chat with your PDFs securely. Upload some documents, ask questions, and get answers based only on what's in those files.

### What it does:
- Handles up to 5 PDFs at once.
- Strictly keeps your documents private to your account.
- Uses MongoDB Atlas for everything (Users, Logs, Vectors).
- Super easy to deploy for free.

### Setup 

1. **Get your keys:**
   - Put your `GROQ_API_KEY` and `MONGODB_URI` in a `.env` file.
   - Use the `.env.example` as a template.

2. **Run the Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

3. **Run the Frontend:**
   ```bash
   cd frontend
   pip install -r requirements.txt
   streamlit run app.py
   ```

   ## Thank You
