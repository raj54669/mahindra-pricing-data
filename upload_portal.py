import streamlit as st
import pandas as pd
import camelot
import io
import re
import tempfile
import os
import fitz  # PyMuPDF
from github import Github
from datetime import datetime
from difflib import get_close_matches

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
    if pd.isna(value):
        return ""
    return re.sub(r'[^0-9]', '', str(value))

def clean_dataframe(df):
    df = df.dropna(how='all')
    df.columns = df.iloc[0]
    df = df[1:].copy()
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.loc[:, df.columns.notna()]
    df = df.reset_index(drop=True)
    return df

def map_headers(columns, target_columns):
    matched = {}
    for col in columns:
        close = get_close_matches(col.strip(), target_columns[2:], n=1, cutoff=0.6)
        if close:
            matched[col] = close[0]
    return matched

def parse_pdf(filepath, model, date_str, target_columns):
    all_data = []
    for flavor in ['lattice', 'stream']:
        tables = camelot.read_pdf(filepath, pages='all', flavor=flavor, strip_text="\n")
        for table in tables:
            df = table.df
            if df.empty or len(df.columns) < 5:
                continue
            df = clean_dataframe(df)
            matched_headers = map_headers(df.columns, target_columns)
            if len(matched_headers) >= 5:
                df = df.rename(columns=matched_headers)
                df = df[[*matched_headers.values()]]
                df.insert(0, 'Price List D.', date_str)
                df.insert(0, 'Model', model)
                for col in df.columns:
                    df[col] = df[col].apply(clean_currency)
                for col in target_columns:
                    if col not in df.columns:
                        df[col] = ""
                df = df[target_columns]
                all_data.append(df)
        if all_data:
            break
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(columns=target_columns)

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
force_reprocess = st.checkbox("🔁 Force reprocess (overwrite if exists)")

if uploaded_files:
    if st.button("🚀 Process Files"):
        master_df = download_master_excel()
        if master_df is None:
            st.stop()

        target_columns = master_df.columns.tolist()

        for file in uploaded_files:
            st.markdown(f"### 🛠️ Processing `{file.name}`")

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
                st.error("❌ No matching tables found in PDF.")
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
