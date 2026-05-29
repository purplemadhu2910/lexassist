import os

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "cleaned_text")
OUTPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "chunks")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

for file in os.listdir(INPUT_FOLDER):
    if file.endswith(".txt"):
        file_path = os.path.join(INPUT_FOLDER, file)

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunks.append(text[start:end])
            start += CHUNK_SIZE - CHUNK_OVERLAP

        for i, chunk in enumerate(chunks):
            chunk_filename = f"{file.replace('.txt', '')}_chunk_{i}.txt"
            chunk_path = os.path.join(OUTPUT_FOLDER, chunk_filename)

            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(chunk)

        print(f"Chunked: {file} → {len(chunks)} chunks")
