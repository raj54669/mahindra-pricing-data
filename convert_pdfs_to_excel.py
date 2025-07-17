import os
import pandas as pd
import pdfplumber
import re

def extract_model_name_from_filename(filename):
    return filename.replace("_JULY25.pdf", "").replace("_", " ").strip()

def extract_rows_from_text(lines):
    rows = []
    for line in lines:
        if not line.strip():
            continue
        if "₹" in line and any(x in line for x in ["MX", "AX"]):
            price_matches = re.findall(r"₹[\d,]+", line)
            if len(price_matches) >= 4:  # crude filter
                rows.append([line.strip()] + price_matches[:4])  # keep first 4 prices
    return rows

def convert_all_pdfs(pdf_folder_path="price-pdfs"):
    all_data = []

    for filename in os.listdir(pdf_folder_path):
        if not filename.endswith(".pdf"):
            continue

        file_path = os.path.join(pdf_folder_path, filename)
        model_name = extract_model_name_from_filename(filename)

        try:
            with pdfplumber.open(file_path) as pdf:
                text_lines = []
                for page in pdf.pages:
                    lines = page.extract_text().split('\n')
                    text_lines.extend(lines)

            extracted_rows = extract_rows_from_text(text_lines)

            if extracted_rows:
                df = pd.DataFrame(
                    extracted_rows,
                    columns=["Variant Info", "Price 1", "Price 2", "Price 3", "Price 4"]
                )
                df.insert(0, "Model Name", model_name)
                all_data.append(df)

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        output_path = os.path.join(pdf_folder_path, "master_price_list.xlsx")
        final_df.to_excel(output_path, index=False)
        return output_path
    else:
        return None
