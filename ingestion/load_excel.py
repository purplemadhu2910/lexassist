import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE, "..", "data", "raw", "excel")
OUTPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "cleaned_text")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

os.makedirs(INPUT_FOLDER, exist_ok=True)

for file in os.listdir(INPUT_FOLDER):
    if not (file.endswith(".xlsx") or file.endswith(".xls") or file.endswith(".csv")):
        continue
    file_path = os.path.join(INPUT_FOLDER, file)
    try:
        df = pd.read_csv(file_path) if file.endswith(".csv") else pd.read_excel(file_path)

        if df.empty:
            print(f"WARN: {file} is empty, skipping.")
            continue

        text = df.to_csv(index=False, sep="\t")
        output_path = os.path.join(OUTPUT_FOLDER, file.rsplit(".", 1)[0] + ".txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Processed: {file}")
    except Exception as e:
        print(f"ERROR processing {file}: {e}")
