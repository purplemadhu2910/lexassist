import os
import sys
import shutil

# Set working directory to project root (where this script lives)
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

print("=== LexAssist Build Script ===")
print(f"Working directory: {ROOT}")

# Step 1: Copy raw txt files into cleaned_text
print("\n[1/5] Copying raw text files...")
raw_txt_dir = os.path.join(ROOT, "data", "raw")
cleaned_dir = os.path.join(ROOT, "data", "processed", "cleaned_text")
os.makedirs(cleaned_dir, exist_ok=True)
for f in os.listdir(raw_txt_dir):
    if f.endswith(".txt"):
        shutil.copy(os.path.join(raw_txt_dir, f), os.path.join(cleaned_dir, f))
        print(f"  Copied: {f}")

# Step 2: Load PDFs
print("\n[2/5] Processing PDFs...")
exec(open(os.path.join(ROOT, "ingestion", "load_pdfs.py")).read())

# Step 3: Load JSONs
print("\n[3/5] Processing JSONs...")
exec(open(os.path.join(ROOT, "ingestion", "load_json.py")).read())

# Step 4: Load Excel/CSV
print("\n[4/5] Processing Excel/CSV...")
exec(open(os.path.join(ROOT, "ingestion", "load_excel.py")).read())

# Step 5: Chunk text
print("\n[5/5] Chunking text...")
exec(open(os.path.join(ROOT, "ingestion", "chunk_text.py")).read())

# Step 6: Build FAISS index
print("\n[6/6] Building FAISS index...")
sys.path.insert(0, os.path.join(ROOT, "backend"))
exec(open(os.path.join(ROOT, "backend", "build_index.py")).read())

print("\n=== Build complete! ===")
