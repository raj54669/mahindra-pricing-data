import os
import pandas as pd
import re
from PyPDF2 import PdfReader

def extract_rows_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    rows = []
    for page in reader.pages:
        text = page.extract_text()
        lines = text.split('\n')
        for line in lines:
            # Example pattern: adjust it to fit your actual data
            match = re.match(
                r'^(.*?)\s+₹ ([\d,]+)\s+₹ ([\d,]+)\s+₹ ([\d,]+)\s+₹ ([\d,]+).*',
                line
            )
            if match:
                rows.append([
                    match.group(1).strip(),
                    match.group(2).replace(',', ''),
                    match.group(3).replace(',', ''),
                    match.group(4).replace(',', ''),
                    match.group(5).replace(',', ''),
                ])
    return rows

def convert_all_pdfs(pdf_folder):
    all_rows = []
    for filename in os.listdir(pdf_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            rows = extract_rows_from_pdf(pdf_path)
            all_rows.extend(rows)

    if all_rows:
        df = pd.DataFrame(all_rows, columns=[
            "Model", "Ex-showroom", "Insurance", "Road Tax", "Other"
        ])
        excel_path = "master_sheet.xlsx"
        df.to_excel(excel_path, index=False)
        return excel_path
    else:
        return None
