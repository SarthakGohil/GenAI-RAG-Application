"""SecureRAG — premium dark-themed Streamlit client with JWT auth, PDF upload, Q&A, summarize."""
import os
import streamlit as st
import requests
import time

API = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

def safe_request(method, url, **kwargs):
    """Wrapper for requests with automatic retries for Render's cold starts (502 error)."""
    max_retries = 3
    retry_delay = 5  # seconds
    
    # Increase default timeout to 30s to allow Render to wake up
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30
        
    for i in range(max_retries):
        try:
            r = requests.request(method, url, **kwargs)
            # If we get a 502/503/504, the server might be waking up
            if r.status_code in [502, 503, 504] and i < max_retries - 1:
                with st.spinner(f"Server is waking up (Attempt {i+1}/3)..."):
                    time.sleep(retry_delay)
                    continue
            return r
        except (requests.ConnectionError, requests.Timeout):
            if i < max_retries - 1:
                with st.spinner(f"Connecting to server (Attempt {i+1}/3)..."):
                    time.sleep(retry_delay)
                    continue
            raise
    return requests.request(method, url, **kwargs)  # Final attempt

st.set_page_config(page_title="SecureRAG", page_icon="🔐", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #09090b 0%, #18181b 50%, #09090b 100%); }
.login-card {
    background: rgba(24, 24, 27, 0.7); border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px; padding: 2.5rem; backdrop-filter: blur(16px);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    max-width: 420px; margin: 4rem auto;
}
.brand-header { text-align: center; margin-bottom: 2rem; }
.brand-header h1 { font-size: 2.2rem; font-weight: 700; color: #e2e8f0; margin:0; }
.brand-header p { color: #a1a1aa; margin: 0.3rem 0 0 0; font-size: 0.9rem; }
.answer-box {
    background: rgba(99,102,241,0.05); border-left: 3px solid #6366f1;
    border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem;
    color: #e2e8f0; line-height: 1.7; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}
.user-badge {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white; padding: 0.25rem 0.75rem; border-radius: 20px;
    font-size: 0.8rem; font-weight: 600; display: inline-block;
}
.metric-chip {
    background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.2);
    color: #10b981; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem;
}
section[data-testid="stSidebar"] { background: rgba(9, 9, 11, 0.95) !important; border-right: 1px solid rgba(255,255,255,0.05); }
div[data-baseweb="input"] { background-color: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; }
div[data-testid="stTabs"] button { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Login screen ──────────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.markdown('<div class="login-card"><div class="brand-header"><h1>🔐 SecureRAG</h1><p>Secure document intelligence platform</p></div>', unsafe_allow_html=True)
    ltab, rtab = st.tabs(["Sign In", "Create Account"])
    
    with ltab:
        lu = st.text_input("Username", placeholder="admin", key="lu")
        lp = st.text_input("Password", type="password", placeholder="••••••••", key="lp")
        if st.button("Sign In →", type="primary", use_container_width=True, key="lbtn"):
            if lu and lp:
                with st.spinner("Authenticating…"):
                    try:
                        r = safe_request("POST", f"{API}/login", json={"username": lu, "password": lp}, timeout=30)
                    except requests.RequestException:
                        st.error("Cannot reach API server.")
                    else:
                        if r.status_code == 200:
                            st.session_state.token = r.json()["token"]
                            st.session_state.username = lu
                            st.rerun()
                        else:
                            try:
                                err = r.json().get("detail", "Invalid credentials")
                            except Exception:
                                err = f"Server Error: {r.status_code}. The backend might be experiencing issues."
                            st.error(err)
                            
    with rtab:
        ru = st.text_input("New Username", placeholder="e.g. analyst", key="ru")
        rp = st.text_input("New Password", type="password", placeholder="••••••••", key="rp")
        if st.button("Register", type="primary", use_container_width=True, key="rbtn"):
            if ru and rp:
                with st.spinner("Creating account…"):
                    try:
                        r = safe_request("POST", f"{API}/register", json={"username": ru, "password": rp}, timeout=30)
                    except requests.RequestException:
                        st.error("Cannot reach API server.")
                    else:
                        if r.status_code == 200:
                            st.success("Account created successfully! Automatically signing in...")
                            try:
                                login_r = safe_request("POST", f"{API}/login", json={"username": ru, "password": rp}, timeout=30)
                                if login_r.status_code == 200:
                                    st.session_state.token = login_r.json()["token"]
                                    st.session_state.username = ru
                                    st.rerun()
                                else:
                                    st.error("Auto-login failed. Please sign in manually.")
                            except requests.RequestException:
                                st.error("Cannot reach API server for auto-login.")
                        else:
                            try:
                                err = r.json().get("detail", "Registration failed")
                            except Exception:
                                err = f"Server Error: {r.status_code}. The backend might be experiencing issues."
                            st.error(err)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="margin-bottom:1rem"><span class="user-badge">👤 {st.session_state.get("username","user")}</span></div>', unsafe_allow_html=True)
    st.markdown("**SecureRAG** v1.0")
    st.markdown("Hybrid BM25 + ChromaDB · Cross-encoder reranking · Groq Llama-3.1")
    st.divider()
    if st.button("🔎 Health Check"):
        try:
            h = safe_request("GET", f"{API}/health", timeout=10).json()
            st.json(h)
        except Exception as e:
            st.error(str(e))
    if st.button("🧹 Clear Chat", type="secondary"):
        st.session_state.chat_history = []
        st.session_state.history = []
        st.rerun()
    if st.button("🔓 Logout", type="secondary"):
        st.session_state.clear(); st.rerun()
    
    if "history" not in st.session_state:
        # Try to load from backend
        try:
            hdrs = {"Authorization": f"Bearer {st.session_state.token}"}
            r = safe_request("GET", f"{API}/history", headers=hdrs, timeout=10)
            if r.status_code == 200:
                hist = r.json().get("history", [])
                st.session_state.history = [h["question"] for h in hist][::-1]  # reverse to get oldest to newest since we append
            else:
                st.session_state.history = []
        except:
            st.session_state.history = []

    if "history" in st.session_state and st.session_state.history:
        st.divider()
        st.markdown("**Recent questions**")
        for item in st.session_state.history[-5:][::-1]:
            st.caption(f"• {item[:60]}…" if len(item) > 60 else f"• {item}")

# ── Main tabs ──────────────────────────────────────────────────────────────────
st.markdown('<h2 style="color:#e2e8f0;margin-bottom:0.2rem">🔐 SecureRAG</h2><p style="color:#94a3b8;margin-top:0">Document Intelligence Platform</p>', unsafe_allow_html=True)
hdrs = {"Authorization": f"Bearer {st.session_state.token}"}
t1, t2, t3, t4 = st.tabs(["🤖 Q&A", "📄 Upload PDF", "📊 Summarize", "👤 Profile"])

with t1:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if q := st.chat_input("Ask your document anything..."):
        st.session_state.chat_history.append({"role": "user", "content": q})
        st.session_state.history = st.session_state.get("history", []) + [q]
        
        with st.chat_message("user"):
            st.markdown(q)
            
        with st.chat_message("assistant"):
            ph = st.empty()
            with st.spinner("Retrieving context and thinking..."):
                try:
                    r = safe_request("POST", f"{API}/query", json={"question": q}, headers=hdrs, timeout=120)
                except requests.RequestException as e:
                    ph.error(f"Network error: {e}")
                else:
                    if r.status_code == 200:
                        ans = r.json().get("answer", "")
                        ph.markdown(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    elif r.status_code == 401:
                        st.warning("Session expired."); del st.session_state.token; st.rerun()
                    else:
                        ph.error(r.text)

with t2:
    st.markdown("Upload up to 5 PDFs — they will be parsed, chunked, and added to your vector index.")
    ups = st.file_uploader("Choose PDFs (max ~200 MB each)", type=["pdf"], accept_multiple_files=True)
    if st.button("📥 Ingest into Index", key="up_btn") and ups:
        if len(ups) > 5:
            st.error("Please upload a maximum of 5 documents at once.")
        else:
            with st.spinner(f"Parsing and indexing {len(ups)} file(s)…"):
                total_added = 0
                for up in ups:
                    try:
                        r = safe_request("POST", f"{API}/upload", files={"file": (up.name, up.getvalue(), "application/pdf")}, headers=hdrs, timeout=300)
                    except requests.RequestException as e:
                        st.error(f"Network error for {up.name}: {str(e)}")
                    else:
                        if r.status_code == 200:
                            n = r.json().get("chunks_added", 0)
                            total_added += n
                            st.success(f"✅ Indexed **{n}** chunks from `{up.name}`")
                        elif r.status_code == 401:
                            del st.session_state.token; st.rerun()
                        else:
                            st.error(f"Failed to index {up.name}: {r.text}")
                if total_added > 0:
                    st.toast(f"Successfully processed {total_added} chunks from {len(ups)} files!", icon='🚀')

with t3:
    st.markdown("Generate a retrieval-grounded summary of the indexed documents.")
    focus = st.text_input("Optional focus (e.g. risks, CVEs, compliance)", placeholder="key vulnerabilities and attack vectors")
    if st.button("📊 Generate Summary", key="sum_btn", type="primary"):
        with st.spinner("Summarizing from index…"):
            try:
                r = safe_request("POST", f"{API}/summarize", json={"focus": focus}, headers=hdrs, timeout=120)
            except requests.RequestException as e:
                st.error(str(e))
            else:
                if r.status_code == 200:
                    st.markdown(f'<div class="answer-box">{r.json().get("summary","")}</div>', unsafe_allow_html=True)
                elif r.status_code == 401:
                    del st.session_state.token; st.rerun()
                else:
                    st.error(r.text)

with t4:
    st.markdown("### 👤 User Profile")
    st.markdown(f"**Username:** `{st.session_state.get('username', 'user')}`")
    st.markdown("---")
    st.markdown("#### Database Audit Logs")
    if st.button("🔄 Fetch My History", type="secondary"):
        with st.spinner("Fetching logs from MongoDB..."):
            try:
                r = safe_request("GET", f"{API}/history", headers=hdrs, timeout=10)
            except requests.RequestException:
                st.error("Network error")
            else:
                if r.status_code == 200:
                    hist = r.json().get("history", [])
                    if not hist:
                        st.info("No audit logs found for this user.")
                    else:
                        for idx, h in enumerate(hist):
                            with st.expander(f"Log #{idx+1} | {h.get('question','')[:50]}..."):
                                st.markdown(f"**Query:** {h.get('question')}")
                                st.markdown(f"**Answer Preview:** {h.get('answer')}")
                elif r.status_code == 401:
                    del st.session_state.token; st.rerun()
                else:
                    st.error(r.text)
