import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
import tempfile
import os
import fitz  # PyMuPDF
from github import Github
from datetime import datetime

# --- ENV Secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
GITHUB_BRANCH = st.secrets["GITHUB_BRANCH"]
PDF_UPLOAD_PATH = st.secrets["PDF_UPLOAD_PATH"]
EXCEL_FILE_PATH = st.secrets["EXCEL_PATH"]

# --- GitHub Helper ---
def get_repo():
    g = Github(GITHUB_TOKEN)
    return g.get_repo(GITHUB_REPO)

def download_master_excel():
    repo = get_repo()
    try:
        contents = repo.get_contents(EXCEL_FILE_PATH, ref=GITHUB_BRANCH)
        df = pd.read_excel(io.BytesIO(contents.decoded_content))
        return df
    except Exception:
        st.warning("Master Excel not found in GitHub. Creating a new one.")
        return None

def upload_to_github(filepath, github_path):
    repo = get_repo()
    with open(filepath, "rb") as file:
        content = file.read()
    try:
        contents = repo.get_contents(github_path, ref=GITHUB_BRANCH)
        repo.update_file(contents.path, f"Update {github_path}", content, contents.sha, branch=GITHUB_BRANCH)
    except Exception:
        repo.create_file(github_path, f"Add {github_path}", content, branch=GITHUB_BRANCH)

# --- PDF Parser ---
def extract_date_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()

    match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date()
        except:
            return None
    return None

def clean_currency(value):
    return re.sub(r'[\u20B9,\s]', '', value).strip()

def extract_structured_rows(lines):
    rows = []
    for line in lines:
        tokens = re.split(r'\s{2,}', line.strip())
        if len(tokens) == 10 and any(char.isdigit() for char in tokens[2]):
            rows.append(tokens)
    return rows

def parse_pdf(filepath, model, date_str, target_columns):
    extracted_data = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            rows = extract_structured_rows(lines)
            for tokens in rows:
                row = {
                    "Model": model,
                    "Price List D.": date_str,
                    target_columns[2]: tokens[0],
                    target_columns[3]: tokens[1],
                    target_columns[4]: clean_currency(tokens[2]),
                    target_columns[5]: clean_currency(tokens[3]),
                    target_columns[6]: clean_currency(tokens[4]),
                    target_columns[7]: clean_currency(tokens[5]),
                    target_columns[8]: clean_currency(tokens[6]),
                    target_columns[9]: clean_currency(tokens[7]),
                    target_columns[10]: clean_currency(tokens[8]),
                    target_columns[11]: clean_currency(tokens[9]),
                }
                extracted_data.append(row)
    return pd.DataFrame(extracted_data, columns=target_columns)

# --- Streamlit UI ---
st.set_page_config(page_title="Mahindra Price List Uploader")
st.title("\U0001F697 Mahindra Price List Uploader")

with st.sidebar:
    st.markdown("### \U0001F4C2 Upload History")
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if st.session_state["history"]:
        for entry in st.session_state["history"]:
            st.markdown(f"- {entry}")
    else:
        st.markdown("No entries yet.")

    if os.path.exists("master_data.xlsx"):
        with open("master_data.xlsx", "rb") as f:
            st.download_button("⬇️ Download Master Excel", f, file_name="master_data.xlsx")

uploaded_files = st.file_uploader("Upload Mahindra Price List PDFs", type="pdf", accept_multiple_files=True)
force_reprocess = st.checkbox("\U0001F501 Force reprocess (overwrite if exists)")

if uploaded_files:
    if st.button("\U0001F680 Process Files"):
        master_df = download_master_excel()
        if master_df is None:
            st.stop()

        target_columns = master_df.columns.tolist()

        for file in uploaded_files:
            st.markdown(f"### \U0001F6E0️ Processing `{file.name}`")

            model = re.sub(r'_JULY25.*$', '', file.name).strip().replace('_', ' ')

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name

            date_obj = extract_date_from_pdf(tmp_path)
            if not date_obj:
                st.error("❌ Could not extract date from PDF.")
                continue

            df_new = parse_pdf(tmp_path, model, date_obj, target_columns)

            if df_new.empty:
                st.error("❌ No structured rows extracted from PDF.")
                continue

            master_df = download_master_excel()

            duplicate_check = (master_df['Model'] == model) & (master_df['Price List D.'] == pd.to_datetime(date_obj))

            if duplicate_check.any():
                if force_reprocess:
                    master_df = master_df[~duplicate_check]
                    st.warning("⚠️ Duplicate entry found. Overwriting as requested.")
                else:
                    st.warning("⚠️ Duplicate entry. Skipping.")
                    continue

            combined_df = pd.concat([master_df, df_new], ignore_index=True)
            combined_df.to_excel("master_data.xlsx", index=False)

            upload_to_github("master_data.xlsx", EXCEL_FILE_PATH)
            upload_to_github(tmp_path, f"{PDF_UPLOAD_PATH}/{file.name}")

            st.success("✅ File processed and uploaded to GitHub.")
            st.session_state["history"].append(file.name)

            os.remove(tmp_path)
