import streamlit as st
import pandas as pd
from io import BytesIO
from scripts.github_utils import get_github_repo, download_file_from_repo, upload_or_update_file
from scripts.pdf_parser import extract_model, extract_effective_date, parse_table

st.title("📤 Mahindra Price List Uploader")

uploaded_files = st.file_uploader("Upload Mahindra PDF files", type=["pdf"], accept_multiple_files=True)

if st.button("Process Files") and uploaded_files:
    repo = get_github_repo()
    excel_path = st.secrets["github"]["excel_path"]
    pdf_dir = st.secrets["github"]["pdf_dir"]

    # Load master Excel
    try:
        master_data_io, master_sha = download_file_from_repo(repo, excel_path)
        df_master = pd.read_excel(master_data_io)
    except:
        df_master = pd.DataFrame()

    for uploaded in uploaded_files:
        st.markdown(f"#### 🔍 Processing `{uploaded.name}`")

        model = extract_model(uploaded.name)
        uploaded.seek(0)
        date = extract_effective_date(uploaded)
        uploaded.seek(0)
        df_new = parse_table(uploaded)
        uploaded.seek(0)

        if df_new is None or not date:
            st.error("❌ Could not extract data or table.")
            continue

        # Add metadata columns
        df_new.insert(0, "Price List D.", date)
        df_new.insert(0, "Model", model)

        # Duplicate check
        if not df_master[
            (df_master["Model"] == model) &
            (df_master["Price List D."] == date)
        ].empty:
            st.warning("⚠️ This data already exists. Skipping.")
            continue

        df_master = pd.concat([df_master, df_new], ignore_index=True)

        # Save master Excel
        output = BytesIO()
        df_master.to_excel(output, index=False)
        upload_or_update_file(repo, excel_path, output, f"Update master with {model} {date}")

        # Save PDF
        upload_or_update_file(repo, f"{pdf_dir}/{uploaded.name}", uploaded, f"Add raw PDF: {uploaded.name}")

        st.success(f"✅ Uploaded `{uploaded.name}` successfully.")
