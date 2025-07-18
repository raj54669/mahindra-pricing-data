import camelot
import pdfplumber
from PyPDF2 import PdfReader
import pandas as pd
import tempfile
import os
from io import BytesIO

def extract_model(filename: str):
    return filename.replace("_JULY25.pdf", "").replace("_", " ").strip()

def extract_effective_date(pdf_file: BytesIO) -> str:
    reader = PdfReader(pdf_file)
    text = reader.pages[0].extract_text()
    for line in text.splitlines():
        if "w.e.f." in line:
            date_part = line.split("w.e.f.")[-1].strip()
            return date_part
    return None

def parse_table(pdf_file: BytesIO) -> pd.DataFrame:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    tables = camelot.read_pdf(tmp_path, pages='all', flavor='stream')
    os.remove(tmp_path)

    if tables.n == 0:
        return None

    df = pd.concat([t.df for t in tables], ignore_index=True)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    return df
