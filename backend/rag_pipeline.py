import os
from typing import Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.retrievers import EnsembleRetriever
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from config import MONGODB_VECTOR_COLLECTION, MONGODB_VECTOR_INDEX
from database import get_db
from llm_factory import get_chat_llm

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Use Cloud-based embeddings to save RAM on Render (512MB limit)
_hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
_embeddings = HuggingFaceEndpointEmbeddings(
    huggingfacehub_api_token=_hf_key, 
    model="sentence-transformers/all-MiniLM-L6-v2"
)

# Lazy-loaded vector store
_vector_store: MongoDBAtlasVectorSearch | None = None
_retrievers: dict[str, Any] = {}
_qa_chains: dict[str, Any] = {}
_sum_chains: dict[str, Any] = {}


def get_vector_store() -> MongoDBAtlasVectorSearch:
    global _vector_store
    if _vector_store is None:
        db = get_db()
        if db is None:
            raise RuntimeError("MongoDB is not connected. Vector search unavailable.")
        _collection = db[MONGODB_VECTOR_COLLECTION]
        _vector_store = MongoDBAtlasVectorSearch(
            collection=_collection,
            embedding=_embeddings,
            index_name=MONGODB_VECTOR_INDEX,
            relevance_score_fn="cosine",
        )
    return _vector_store


def invalidate_rag_cache() -> None:
    _retrievers.clear()
    _qa_chains.clear()
    _sum_chains.clear()


def _get_all_docs(username: str, limit: int = 4000) -> list[Document]:
    """Fetch all documents for a user from MongoDB to build BM25 index."""
    db = get_db()
    if db is None:
        return []
    coll = db[MONGODB_VECTOR_COLLECTION]
    # Check both top-level and metadata nested field to be absolutely sure
    cursor = coll.find({
        "$or": [
            {"metadata.uploaded_by": username},
            {"uploaded_by": username}
        ]
    }).limit(limit)
    out: list[Document] = []
    for doc in cursor:
        # Check both LangChain standard 'text' field and our custom metadata.text
        text = doc.get("text") or doc.get("page_content") or doc.get("metadata", {}).get("text")
        if text and str(text).strip():
            source = doc.get("metadata", {}).get("source", "Unknown")
            out.append(Document(page_content=str(text), metadata={"source": source, "uploaded_by": username}))
    return out


def _build_retriever(username: str):
    # Vector Search with pre-filter for user isolation
    vs = get_vector_store()
    # Try multiple common metadata filter patterns for MongoDBAtlasVectorSearch
    base = vs.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 20, # Increased further
            "pre_filter": {
                "metadata.uploaded_by": {"$eq": username}
            }
        }
    )
    
    # Optional Hybrid BM25 fallback
    docs = _get_all_docs(username)
    if len(docs) >= 1: # Always try to use BM25 if there's at least 1 doc
        bm25 = BM25Retriever.from_documents(docs)
        bm25.k = 20
        # Give BM25 more weight as it's better at finding exact keywords like "multiclient" vs "p2p"
        return EnsembleRetriever(retrievers=[bm25, base], weights=[0.7, 0.3])
    
    return base


def _get_retriever(username: str):
    if username not in _retrievers:
        _retrievers[username] = _build_retriever(username)
    return _retrievers[username]


def get_rag_chain(username: str):
    if username not in _qa_chains:
        retriever = _get_retriever(username)
        llm = get_chat_llm(0.2) # Lower temperature for better accuracy
        system = (
            "You are a helpful AI assistant. Use the provided context to answer the user's question. "
            "The context includes lab reports and technical notes. If the information is in the context, "
            "provide a detailed answer. If you cannot find the answer, say you don't know, but "
            "always check all provided context carefully.\n\n{context}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [("system", system), ("human", "{input}")]
        )
        combine = create_stuff_documents_chain(llm, prompt)
        _qa_chains[username] = create_retrieval_chain(retriever, combine)
    return _qa_chains[username]


def get_summarize_chain(username: str):
    if username not in _sum_chains:
        retriever = _get_retriever(username)
        llm = get_chat_llm(0.2)
        system = (
            "You are summarizing multiple lab assignments from the provided context. "
            "Start with a high-level overview of ALL documents in the context. "
            "Then break down by specific file source if possible. "
            "If the provided context is empty or missing, DO NOT imagine content; instead, "
            "say exactly: 'Error: Context is missing or empty. Please ensure documents are uploaded.'\n\n{context}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [("system", system), ("human", "{input}")]
        )
        combine = create_stuff_documents_chain(llm, prompt)
        _sum_chains[username] = create_retrieval_chain(retriever, combine)
    return _sum_chains[username]



