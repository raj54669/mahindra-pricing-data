import streamlit as st
import pandas as pd
from io import BytesIO
from scripts.github_utils import (
    get_github_repo,
    download_file_from_repo,
    upload_or_update_file
)
from scripts.pdf_parser import (
    extract_model,
    extract_effective_date,
    parse_table
)

st.set_page_config(page_title="Mahindra PDF Uploader", layout="centered")
st.title("🚘 Mahindra Price List Uploader")

# ---- GitHub repo info from secrets
repo = get_github_repo()
excel_path = st.secrets["EXCEL_PATH"]
pdf_dir = st.secrets["PDF_UPLOAD_PATH"]

# ---- Upload UI
uploaded_files = st.file_uploader(
    "📄 Upload Mahindra Price List PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button("🚀 Process Files") and uploaded_files:
    # Load master Excel (or create new)
    try:
        master_io, master_sha = download_file_from_repo(repo, excel_path)
        df_master = pd.read_excel(master_io)
    except Exception:
        st.warning("Master Excel not found in GitHub. Creating a new one.")
        df_master = pd.DataFrame(columns=["Model", "Price List D."])  # Will expand dynamically

    for uploaded in uploaded_files:
        st.markdown(f"---\n### 🛠 Processing `{uploaded.name}`")

        # Extract metadata
        model = extract_model(uploaded.name)
        uploaded.seek(0)
        effective_date = extract_effective_date(uploaded)
        uploaded.seek(0)
        df_new = parse_table(uploaded)
        uploaded.seek(0)

        # Validate
        if not effective_date:
            st.error("❌ Could not extract effective date.")
            continue
        if df_new is None or df_new.empty:
            st.error("❌ No valid table extracted from PDF.")
            continue

        # Check for duplicates
        duplicate = not df_master[
            (df_master["Model"] == model) &
            (df_master["Price List D."] == effective_date)
        ].empty
        if duplicate:
            st.warning("⚠️ This file has already been processed. Skipping.")
            continue

        # Add metadata columns
        df_new.insert(0, "Price List D.", effective_date)
        df_new.insert(0, "Model", model)

        # Append to master
        df_master = pd.concat([df_master, df_new], ignore_index=True)

        # Save updated Excel to GitHub
        try:
            output_excel = BytesIO()
            df_master.to_excel(output_excel, index=False)
            upload_or_update_file(repo, excel_path, output_excel, f"Update master_data.xlsx with {model} {effective_date}")
        except Exception as e:
            st.error(f"❌ Failed to update Excel on GitHub: {e}")
            continue

        # Upload raw PDF to GitHub
        try:
            upload_or_update_file(repo, f"{pdf_dir}/{uploaded.name}", uploaded, f"Upload PDF: {uploaded.name}")
        except Exception as e:
            st.error(f"❌ Failed to upload PDF to GitHub: {e}")
            continue

        st.success(f"✅ Successfully processed `{uploaded.name}`")

