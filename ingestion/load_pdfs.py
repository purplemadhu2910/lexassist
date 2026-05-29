import os
import pdfplumber

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE, "..", "data", "raw", "pdf")
OUTPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "cleaned_text")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_pdf_text(file_path):
    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
    return "\n".join(pages_text) + "\n" if pages_text else ""

for file in os.listdir(INPUT_FOLDER):
    if file.endswith(".pdf"):
        file_path = os.path.join(INPUT_FOLDER, file)
        text = extract_pdf_text(file_path)

        output_path = os.path.join(OUTPUT_FOLDER, file.replace(".pdf", ".txt"))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Processed: {file}")
