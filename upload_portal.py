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

# ---- Load master Excel
try:
    master_io, master_sha = download_file_from_repo(repo, excel_path)
    df_master = pd.read_excel(master_io)
except Exception:
    st.warning("⚠️ Master Excel not found in GitHub. Creating a new one.")
    df_master = pd.DataFrame(columns=["Model", "Price List D."])  # Fallback columns

# ---- Sidebar: Upload history + Excel download
with st.sidebar:
    st.header("📂 Upload History")
    if df_master.empty:
        st.info("No entries yet.")
    else:
        recent = df_master[["Model", "Price List D."]].drop_duplicates().tail(10)
        st.write("### 🔄 Recent Uploads")
        st.dataframe(recent, use_container_width=True)

        st.markdown("### 📥 Download Master Excel")
        download_buf = BytesIO()
        df_master.to_excel(download_buf, index=False)
        st.download_button(
            label="⬇️ Download master_data.xlsx",
            data=download_buf,
            file_name="master_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown(f"📊 **Total Records:** `{len(df_master)}`")

# ---- File upload UI
uploaded_files = st.file_uploader(
    "📄 Upload Mahindra Price List PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

# ---- Helper to make columns unique
def make_columns_unique(columns):
    seen = {}
    result = []
    for col in columns:
        if col not in seen:
            seen[col] = 1
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}.{seen[col]-1}")
    return result

# ---- Process uploaded files
if st.button("🚀 Process Files") and uploaded_files:
    for uploaded in uploaded_files:
        st.markdown(f"---\n### 🛠 Processing `{uploaded.name}`")

        # Step 1: Extract metadata
        model = extract_model(uploaded.name)
        uploaded.seek(0)
        effective_date = extract_effective_date(uploaded)
        uploaded.seek(0)
        df_new = parse_table(uploaded)
        uploaded.seek(0)

        # Step 2: Validation
        if not effective_date:
            st.error("❌ Could not extract effective date.")
            continue
        if df_new is None or df_new.empty:
            st.error("❌ No valid table extracted from PDF.")
            continue

        # Step 3: Duplicate check
        duplicate = not df_master[
            (df_master["Model"] == model) &
            (df_master["Price List D."] == effective_date)
        ].empty
        if duplicate:
            st.warning("⚠️ This file has already been processed. Skipping.")
            continue

        # Step 4: Add metadata columns
        df_new.insert(0, "Price List D.", effective_date)
        df_new.insert(0, "Model", model)

        # Step 5: Fix column issues
        df_new.columns = make_columns_unique(df_new.columns)
        df_master.columns = make_columns_unique(df_master.columns)
        common_cols = [col for col in df_master.columns if col in df_new.columns]
        df_new = df_new[common_cols]
        df_master = df_master[common_cols]

        # Step 6: Append and save
        df_master = pd.concat([df_master, df_new], ignore_index=True)

        try:
            output_excel = BytesIO()
            df_master.to_excel(output_excel, index=False)
            upload_or_update_file(
                repo, excel_path, output_excel,
                f"Update master_data.xlsx with {model} {effective_date}"
            )
        except Exception as e:
            st.error(f"❌ Failed to update Excel on GitHub: {e}")
            continue

        # Step 7: Upload raw PDF
        try:
            upload_or_update_file(
                repo, f"{pdf_dir}/{uploaded.name}", uploaded,
                f"Upload PDF: {uploaded.name}"
            )
        except Exception as e:
            st.error(f"❌ Failed to upload PDF to GitHub: {e}")
            continue

        st.success(f"✅ Successfully processed `{uploaded.name}`")
