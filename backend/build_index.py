import os
import pickle
import faiss
import numpy as np
from fastembed import TextEmbedding

CHUNKS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "chunks")
RAW_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "index.faiss")
CHUNKS_META_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vector_store", "chunks_meta.pkl")

def build_index():
    texts = []

    # Load processed chunks
    print("Loading processed chunks...")
    chunks_path = os.path.abspath(CHUNKS_FOLDER)
    for filename in sorted(os.listdir(chunks_path)):
        if filename.endswith(".txt"):
            filepath = os.path.join(chunks_path, filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if content:
                texts.append(content)

    # Load extra raw txt files (business, gst, rent, contracts, startup, tax)
    print("Loading extra raw text files...")
    raw_path = os.path.abspath(RAW_FOLDER)
    for filename in sorted(os.listdir(raw_path)):
        if filename.endswith(".txt"):
            filepath = os.path.join(raw_path, filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if content:
                texts.append(content)

    print(f"Total texts to index: {len(texts)}")
    print("Generating embeddings...")

    model = TextEmbedding("BAAI/bge-small-en-v1.5")
    embeddings = list(model.embed(texts))
    import numpy as np
    embeddings = np.array(embeddings).astype("float32")

    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    faiss.write_index(index, os.path.abspath(INDEX_PATH))

    with open(os.path.abspath(CHUNKS_META_PATH), "wb") as f:
        pickle.dump(texts, f)

    print(f"Done. {len(texts)} texts indexed and saved.")

if __name__ == "__main__":
    build_index()
