import os
import pdfplumber
import pandas as pd

INPUT_FOLDER = "price-pdfs"
OUTPUT_FILE = "PV Price List Master.xlsx"

all_tables = []

for filename in os.listdir(INPUT_FOLDER):
    if filename.endswith(".pdf"):
        filepath = os.path.join(INPUT_FOLDER, filename)
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table)
                    all_tables.append(df)

# Combine all tables and clean (you can customize this part)
if all_tables:
    final_df = pd.concat(all_tables, ignore_index=True)
    final_df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Saved: {OUTPUT_FILE}")
else:
    print("❌ No tables found in PDFs.")
