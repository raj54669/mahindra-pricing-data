import os
import pandas as pd
from PyPDF2 import PdfReader  # or use pdfplumber or tabula depending on your actual parser
# import pdfplumber  # Example: if you use pdfplumber

def make_unique_columns(columns):
    seen = {}
    new_columns = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_columns.append(col)
    return new_columns

def convert_all_pdfs(pdf_folder_path="price-pdfs"):
    all_data = []

    for filename in os.listdir(pdf_folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(pdf_folder_path, filename)

            try:
                # Replace the below with your actual logic to extract tables from PDF
                # Example using dummy data to simulate PDF to DataFrame conversion
                df = extract_data_from_pdf(file_path)

                # Ensure column names are unique
                df.columns = make_unique_columns(df.columns)
                all_data.append(df)

            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        output_path = os.path.join(pdf_folder_path, "master_price_list.xlsx")
        combined_df.to_excel(output_path, index=False)
        return output_path
    else:
        return None

# Dummy function for example purposes
def extract_data_from_pdf(pdf_path):
    # You should replace this with actual table extraction logic
    # Example:
    # with pdfplumber.open(pdf_path) as pdf:
    #     first_page = pdf.pages[0]
    #     table = first_page.extract_table()
    #     df = pd.DataFrame(table[1:], columns=table[0])
    #     return df

    # Temporary mock data:
    return pd.DataFrame({
        "Model": ["XUV700", "Thar"],
        "Price": [1500000, 1200000],
        "Region": ["Delhi", "Mumbai"]
    })
