import os

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "cleaned_text")
OUTPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "chunks")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


for file in os.listdir(INPUT_FOLDER):
    if not file.endswith(".txt"):
        continue
    file_path = os.path.join(INPUT_FOLDER, file)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        base_name = file.replace(".txt", "")

        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_chunk_{i}.txt")
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(chunk)

        print(f"Chunked: {file} → {len(chunks)} chunks")
    except Exception as e:
        print(f"ERROR chunking {file}: {e}")
