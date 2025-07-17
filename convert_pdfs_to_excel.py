import os
import pandas as pd
import pdfplumber

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
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        table = page.extract_table()
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])
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
