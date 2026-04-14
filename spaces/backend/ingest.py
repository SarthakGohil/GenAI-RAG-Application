"""PDF extraction (LlamaParse if configured, else PyPDF) and Chroma ingest."""
import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_pipeline import get_vector_store, invalidate_rag_cache
from security import sanitize_filename

_SPLIT = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
_MAX_BYTES = 200 * 1024 * 1024


def _pypdf_text(path: str) -> str:
    docs = PyPDFLoader(path).load()
    return "\n\n".join(d.page_content or "" for d in docs).strip()


def _llama_parse_text(path: str) -> str | None:
    key = os.getenv("LLAMA_CLOUD_API_KEY", "").strip()
    if not key:
        return None
    try:
        import nest_asyncio
        from llama_parse import LlamaParse
    except Exception:
        return None
    nest_asyncio.apply()
    try:
        os.environ["LLAMA_CLOUD_API_KEY"] = key
        parser = LlamaParse(result_type="markdown")
        pages = parser.load_data(path)
    except Exception:
        return None
    parts: list[str] = []
    for p in pages:
        t = getattr(p, "text", None) or getattr(p, "page_content", None)
        if t:
            parts.append(str(t))
    out = "\n\n".join(parts).strip()
    return out or None


def extract_pdf_text(raw: bytes) -> str:
    if len(raw) > _MAX_BYTES:
        raise ValueError("PDF exceeds 200MB limit")
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        text = _llama_parse_text(path) or _pypdf_text(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if not text.strip():
        raise ValueError("No extractable text from PDF")
    return text


def ingest_pdf_bytes(raw: bytes, original_name: str, username: str) -> int:
    text = extract_pdf_text(raw)
    safe = sanitize_filename(original_name)
    # Create chunks from the text
    chunks = _SPLIT.create_documents([text])
    # Apply metadata to each chunk
    for chunk in chunks:
        # Include fields in metadata as LangChain usually stores this as an object
        chunk.metadata = {
            "source": safe, 
            "uploaded_by": username, 
            "text": chunk.page_content  # Help BM25 find it in metadata if needed
        }
    
    get_vector_store().add_documents(chunks)
    invalidate_rag_cache()
    return len(chunks)
