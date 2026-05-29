import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE, "..", "data", "raw", "excel")
OUTPUT_FOLDER = os.path.join(BASE, "..", "data", "processed", "cleaned_text")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for file in os.listdir(INPUT_FOLDER):
    if file.endswith(".xlsx") or file.endswith(".xls") or file.endswith(".csv"):
        file_path = os.path.join(INPUT_FOLDER, file)

        if file.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        text = df.to_csv(index=False, sep="\t")

        output_path = os.path.join(OUTPUT_FOLDER, file.rsplit(".", 1)[0] + ".txt")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Processed: {file}")
