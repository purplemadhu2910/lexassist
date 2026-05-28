import os
import json

INPUT_FOLDER = "data/raw/json"
OUTPUT_FOLDER = "data/processed/cleaned_text"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for file in os.listdir(INPUT_FOLDER):
    if file.endswith(".json"):
        file_path = os.path.join(INPUT_FOLDER, file)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            # Ensure items remain as valid JSON if they are dicts/lists
            text_content = "\n".join(
                json.dumps(item) if isinstance(item, (dict, list)) else str(item)
                for item in data
            ) + "\n"
        else:
            text_content = json.dumps(data, indent=2)

        output_path = os.path.join(
            OUTPUT_FOLDER, file.replace(".json", ".txt")
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        print(f"Processed: {file}")