import os
import pickle
import tempfile
import faiss
import numpy as np
from fastembed import TextEmbedding

CHUNKS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "chunks")
RAW_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "index.faiss")
CHUNKS_META_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "chunks_meta.pkl")


def _load_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def build_index():
    seen = set()
    texts = []

    def add(text: str):
        if text and text not in seen:
            seen.add(text)
            texts.append(text)

    print("Loading processed chunks...")
    for filename in sorted(os.listdir(os.path.abspath(CHUNKS_FOLDER))):
        if filename.endswith(".txt"):
            add(_load_txt(os.path.join(os.path.abspath(CHUNKS_FOLDER), filename)))

    print("Loading extra raw text files...")
    for filename in sorted(os.listdir(os.path.abspath(RAW_FOLDER))):
        if filename.endswith(".txt"):
            add(_load_txt(os.path.join(os.path.abspath(RAW_FOLDER), filename)))

    print(f"Total unique texts to index: {len(texts)}")
    print("Generating embeddings...")

    model = TextEmbedding("BAAI/bge-small-en-v1.5")
    embeddings = np.array(list(model.embed(texts))).astype("float32")

    print("Building FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    vector_store_dir = os.path.dirname(os.path.abspath(INDEX_PATH))
    os.makedirs(vector_store_dir, exist_ok=True)

    # Write FAISS index atomically via a temp file
    index_abs = os.path.abspath(INDEX_PATH)
    fd, tmp_index = tempfile.mkstemp(dir=vector_store_dir, suffix=".faiss")
    os.close(fd)
    try:
        faiss.write_index(index, tmp_index)
        os.replace(tmp_index, index_abs)
    except Exception:
        os.remove(tmp_index)
        raise

    # Write chunks metadata atomically via a temp file
    meta_abs = os.path.abspath(CHUNKS_META_PATH)
    fd, tmp_meta = tempfile.mkstemp(dir=vector_store_dir, suffix=".pkl")
    os.close(fd)
    try:
        with open(tmp_meta, "wb") as f:
            pickle.dump(texts, f)
        os.replace(tmp_meta, meta_abs)
    except Exception:
        os.remove(tmp_meta)
        raise

    print(f"Done. {len(texts)} unique texts indexed and saved.")


if __name__ == "__main__":
    build_index()
