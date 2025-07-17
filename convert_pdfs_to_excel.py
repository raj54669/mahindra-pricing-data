import os
import pdfplumber
import pandas as pd

INPUT_FOLDER = "price-pdfs"
OUTPUT_FILE = "PV Price List Master.xlsx"

merged_data = []

for file_name in os.listdir(INPUT_FOLDER):
    if file_name.endswith(".pdf"):
        file_path = os.path.join(INPUT_FOLDER, file_name)
        print(f"📄 Processing {file_name}")
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        df = pd.DataFrame(table)
                        df["Source_File"] = file_name  # Optional: track which file the row came from
                        merged_data.append(df)
        except Exception as e:
            print(f"❌ Failed to process {file_name}: {e}")

# Combine all data into one Excel file
if merged_data:
    final_df = pd.concat(merged_data, ignore_index=True)
    final_df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Merged Excel saved to {OUTPUT_FILE}")
else:
    print("⚠️ No tables extracted from PDFs.")
