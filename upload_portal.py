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

st.set_page_config(page_title="Mahindra PDF Uploader", layout="wide")
st.title("🚘 Mahindra Price List Uploader")

# ---- GitHub setup
repo = get_github_repo()
excel_path = st.secrets["EXCEL_PATH"]
pdf_dir = st.secrets["PDF_UPLOAD_PATH"]

# ---- Load master Excel (or fallback to local sample)
try:
    master_io, master_sha = download_file_from_repo(repo, excel_path)
    df_master = pd.read_excel(master_io)
except Exception:
    st.warning("⚠️ Master Excel not found in GitHub. Using uploaded sample as base.")
    df_master = pd.read_excel("master_data.xlsx")

# ---- Sidebar: Upload history
with st.sidebar:
    st.header("📂 Upload History")
    if df_master.empty:
        st.info("No entries yet.")
    else:
        recent = df_master[["Model", "Price List D."]].drop_duplicates().tail(10)
        st.write("### 🔄 Recent Uploads")
        st.dataframe(recent, use_container_width=True)

        st.markdown("### 📥 Download Master Excel")
        buf = BytesIO()
        df_master.to_excel(buf, index=False)
        st.download_button("⬇️ Download master_data.xlsx", buf.getvalue(), "master_data.xlsx")

        st.markdown(f"📊 **Total Records:** `{len(df_master)}`")

# ---- Upload UI
uploaded_files = st.file_uploader(
    "📄 Upload Mahindra Price List PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

# ---- Main processing
if st.button("🚀 Process Files") and uploaded_files:
    for uploaded in uploaded_files:
        st.markdown(f"---\n### 🛠 Processing `{uploaded.name}`")

        model = extract_model(uploaded.name)
        uploaded.seek(0)
        effective_date = extract_effective_date(uploaded)
        uploaded.seek(0)
        df_new = parse_table(uploaded)
        uploaded.seek(0)

        if not effective_date or df_new is None or df_new.empty:
            st.error("❌ Failed to extract data from PDF.")
            continue

        # Insert metadata
        df_new.insert(0, "Price List D.", effective_date)
        df_new.insert(0, "Model", model)

        # Normalize column names
        df_new.columns = df_new.columns.str.strip()
        df_master.columns = df_master.columns.str.strip()

        # Validate: All required columns must be present
        if not all(col in df_new.columns for col in df_master.columns):
            missing = [col for col in df_master.columns if col not in df_new.columns]
            st.error(f"❌ Missing columns in parsed data: {missing}")
            continue

        # Check duplicate entry
        is_duplicate = not df_master[
            (df_master["Model"] == model) &
            (df_master["Price List D."] == effective_date)
        ].empty
        if is_duplicate:
            st.warning("⚠️ Duplicate entry. Skipping.")
            continue

        # Align and append
        df_new = df_new[df_master.columns]
        df_master = pd.concat([df_master, df_new], ignore_index=True)

        # Upload Excel to GitHub
        try:
            out_excel = BytesIO()
            df_master.to_excel(out_excel, index=False)
            upload_or_update_file(
                repo, excel_path, out_excel,
                f"Add {model} price list dated {effective_date}"
            )
        except Exception as e:
            st.error(f"❌ Failed to update Excel: {e}")
            continue

        # Upload PDF to GitHub
        try:
            upload_or_update_file(
                repo, f"{pdf_dir}/{uploaded.name}", uploaded,
                f"Upload PDF: {uploaded.name}"
            )
        except Exception as e:
            st.error(f"❌ Failed to upload PDF: {e}")
            continue

        st.success(f"✅ Successfully processed `{uploaded.name}`")
