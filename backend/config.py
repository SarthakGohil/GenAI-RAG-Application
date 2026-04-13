"""Environment-driven settings for SecureRAG backend."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", str(ROOT / "chroma_data"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "rag_assignment_collection")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production-use-openssl-rand")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
# groq | ollama | local (Unsloth 4-bit base + PEFT from LORA_ADAPTER_DIR)
LLM_BACKEND = os.getenv("LLM_BACKEND", "groq").strip().lower()
_ld_raw = os.getenv("LORA_ADAPTER_DIR")
if _ld_raw:
    _ldp = Path(_ld_raw).expanduser()
    LORA_ADAPTER_DIR = str(_ldp if _ldp.is_absolute() else (ROOT / _ldp))
else:
    LORA_ADAPTER_DIR = str(ROOT / "fine_tune_llama_3.2")
LOCAL_BASE_MODEL = os.getenv("LOCAL_BASE_MODEL", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
MONGODB_VECTOR_COLLECTION = os.getenv("MONGODB_VECTOR_COLLECTION", "vectors")
MONGODB_VECTOR_INDEX = os.getenv("MONGODB_VECTOR_INDEX", "vector_index")
DEMO_USERS_JSON = os.getenv(
    "DEMO_USERS_JSON",
    '{"admin":"admin123","analyst":"analyst123"}',
)
