import os
import sys
import shutil
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(label: str, script: str):
    print(f"\n{label}")
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        capture_output=False
    )
    if result.returncode != 0:
        print(f"ERROR: {script} failed with exit code {result.returncode}")
        sys.exit(result.returncode)

print("=== LexAssist Build Script ===")
print(f"Working directory: {ROOT}")

# Step 1: Copy raw txt files into cleaned_text
print("\n[1/6] Copying raw text files...")
raw_txt_dir = os.path.join(ROOT, "data", "raw")
cleaned_dir = os.path.join(ROOT, "data", "processed", "cleaned_text")
os.makedirs(cleaned_dir, exist_ok=True)
if os.path.exists(raw_txt_dir):
    for f in os.listdir(raw_txt_dir):
        if f.endswith(".txt"):
            shutil.copy(os.path.join(raw_txt_dir, f), os.path.join(cleaned_dir, f))
            print(f"  Copied: {f}")

run("[2/6] Processing PDFs...",    os.path.join(ROOT, "ingestion", "load_pdfs.py"))
run("[3/6] Processing JSONs...",   os.path.join(ROOT, "ingestion", "load_json.py"))
run("[4/6] Processing Excel/CSV...", os.path.join(ROOT, "ingestion", "load_excel.py"))
run("[5/6] Chunking text...",      os.path.join(ROOT, "ingestion", "chunk_text.py"))
run("[6/6] Building FAISS index...", os.path.join(ROOT, "backend", "build_index.py"))

print("\n=== Build complete! ===")
