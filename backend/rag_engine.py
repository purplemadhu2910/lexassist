import os
import pickle
import threading
import faiss
from fastembed import TextEmbedding
from typing import List

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INDEX_PATH = os.path.join(_BASE, "data", "vector_store", "index.faiss")
CHUNKS_META_PATH = os.path.join(_BASE, "data", "vector_store", "chunks_meta.pkl")

_model = None
_index = None
_chunks = None
_init_lock = threading.Lock()


def _load_resources() -> bool:
    global _model, _index, _chunks

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

    return True


def search_chunks(query: str, top_k: int = 3) -> List[str]:
    if not _load_resources():
        return []
    query_embedding = list(_model.embed([query]))[0].reshape(1, -1).astype("float32")
    distances, indices = _index.search(query_embedding, top_k)
    return [_chunks[idx] for idx in indices[0] if idx != -1 and idx < len(_chunks)]


def search_chunks_with_sources(query: str, top_k: int = 3):
    """Returns list of (chunk_text, source_label) tuples."""
    if not _load_resources():
        return []
    query_embedding = list(_model.embed([query]))[0].reshape(1, -1).astype("float32")
    distances, indices = _index.search(query_embedding, top_k)
    results = []
    for idx in indices[0]:
        if idx != -1 and idx < len(_chunks):
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
