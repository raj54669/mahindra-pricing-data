import os
import pandas as pd
import pdfplumber
import re
import streamlit as st  # 👈 log to Streamlit UI

def extract_model_name_from_filename(filename):
    return filename.replace("_JULY25.pdf", "").replace("_", " ").strip()

def extract_rows_from_text(lines, debug=False):
    rows = []
    for line in lines:
        if not line.strip():
            continue
        if "₹" in line:
            prices = re.findall(r"₹[\d,]+", line)
            if prices:
                if debug:
                    st.write(f"🟡 Matched Line: `{line}` → `{prices}`")
                rows.append([line.strip()] + prices[:4])
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
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        text_lines.extend(lines)

            st.write(f"📄 **Processing PDF**: `{filename}`")
            st.write("📝 **First 10 lines from PDF:**")
            st.code("\n".join(text_lines[:10]))

            extracted_rows = extract_rows_from_text(text_lines, debug=True)
            st.write(f"✅ Rows found: `{len(extracted_rows)}`")

            if extracted_rows:
                df = pd.DataFrame(
                    extracted_rows,
                    columns=["Variant Info", "Price 1", "Price 2", "Price 3", "Price 4"]
                )
                df.insert(0, "Model Name", model_name)
                all_data.append(df)

        except Exception as e:
            st.error(f"❌ Error reading {filename}: {e}")
            continue

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        output_path = os.path.join(pdf_folder_path, "master_price_list.xlsx")
        final_df.to_excel(output_path, index=False)
        return output_path
    else:
        return None
