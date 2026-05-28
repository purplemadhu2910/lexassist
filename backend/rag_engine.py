import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from typing import List

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "index.faiss")
CHUNKS_META_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "chunks_meta.pkl")

# Load the model and index once when the server starts, not on every request
_model = None
_index = None
_chunks = None

def _load_resources():
    global _model, _index, _chunks

    index_path = os.path.abspath(INDEX_PATH)
    meta_path = os.path.abspath(CHUNKS_META_PATH)

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        return False

    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    if _index is None:
        _index = faiss.read_index(index_path)

    if _chunks is None:
        with open(meta_path, "rb") as f:
            data = pickle.load(f)
            # Support both plain list (rag_1 format) and dict format (build_index.py format)
            _chunks = data if isinstance(data, list) else data["texts"]

    return True

def search_chunks(query: str, top_k: int = 3) -> List[str]:
    if not _load_resources():
        return []

    query_embedding = _model.encode([query]).astype("float32")
    distances, indices = _index.search(query_embedding, top_k)

    results = []
    for idx in indices[0]:
        if idx != -1 and idx < len(_chunks):
            results.append(_chunks[idx])

    return results

def build_context(query: str) -> str:
    relevant_chunks = search_chunks(query, top_k=3)
    if not relevant_chunks:
        return ""
    context = "\n\n---\n\n".join(relevant_chunks)
    # Keeping context under 3000 characters to avoid hitting token limits
    return context[:3000]
