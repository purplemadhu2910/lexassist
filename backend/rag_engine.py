import os
import pickle
import threading
import logging
import faiss
from fastembed import TextEmbedding
from typing import List

logger = logging.getLogger(__name__)

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INDEX_PATH = os.path.join(_BASE, "data", "vector_store", "index.faiss")
CHUNKS_META_PATH = os.path.join(_BASE, "data", "vector_store", "chunks_meta.pkl")

_model = None
_index = None
_chunks = None
_bm25 = None
_init_lock = threading.Lock()


def preload_resources():
    """Eagerly load the FAISS index, BM25 index, and embedding model at startup."""
    loaded = _load_resources()
    if loaded:
        logger.info("RAG resources pre-loaded successfully.")
    else:
        logger.warning("RAG vector store not found — RAG will be disabled until index is built.")


def _load_resources() -> bool:
    global _model, _index, _chunks, _bm25

    index_path = os.path.abspath(INDEX_PATH)
    meta_path = os.path.abspath(CHUNKS_META_PATH)

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        return False

    # Fast path — already loaded
    if _model is not None and _index is not None and _chunks is not None:
        return True

    with _init_lock:
        # Re-check inside lock to avoid double init
        if _model is None:
            _model = TextEmbedding("BAAI/bge-small-en-v1.5")
        if _index is None:
            _index = faiss.read_index(index_path)
        if _chunks is None:
            with open(meta_path, "rb") as f:
                data = pickle.load(f)
                _chunks = data if isinstance(data, list) else data["texts"]
        if _bm25 is None and _chunks:
            try:
                from rank_bm25 import BM25Okapi
                tokenized_corpus = [c.lower().split() for c in _chunks]
                _bm25 = BM25Okapi(tokenized_corpus)
            except Exception as e:
                logger.warning(f"BM25 initialization skipped: {str(e)}")

    return True


def search_chunks(query: str, top_k: int = 3) -> List[str]:
    pairs = search_chunks_with_sources(query, top_k=top_k)
    return [p[0] for p in pairs]


def search_chunks_with_sources(query: str, top_k: int = 3):
    """Returns list of (chunk_text, source_label) tuples using Hybrid FAISS + BM25 search."""
    if not _load_resources():
        return []
    
    selected_indices = []
    
    # 1. FAISS Vector Search
    try:
        query_embedding = list(_model.embed([query]))[0].reshape(1, -1).astype("float32")
        distances, indices = _index.search(query_embedding, top_k)
        for idx in indices[0]:
            if idx != -1 and idx < len(_chunks):
                selected_indices.append(idx)
    except Exception as e:
        logger.error(f"FAISS search error: {e}")

    # 2. BM25 Keyword Search
    if _bm25 is not None:
        try:
            tokenized_query = query.lower().split()
            bm25_scores = _bm25.get_scores(tokenized_query)
            top_bm25_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
            for idx in top_bm25_idx:
                if idx not in selected_indices and bm25_scores[idx] > 0:
                    selected_indices.append(idx)
        except Exception as e:
            logger.error(f"BM25 search error: {e}")

    results = []
    for idx in selected_indices[:top_k]:
        chunk = _chunks[idx]
        label = chunk.strip().replace("\n", " ")[:80].rstrip() + "…"
        results.append((chunk, label))
    return results


def build_context(query: str) -> str:
    chunks = search_chunks(query, top_k=3)
    if not chunks:
        return ""
    return "\n\n---\n\n".join(chunks)[:3000]


def build_context_with_sources(query: str):
    """Returns (context_str, sources_list)."""
    pairs = search_chunks_with_sources(query, top_k=3)
    if not pairs:
        return "", []
    chunks = [p[0] for p in pairs]
    sources = [p[1] for p in pairs]
    return "\n\n---\n\n".join(chunks)[:3000], sources
