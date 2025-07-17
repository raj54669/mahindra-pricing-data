import streamlit as st
import os
from convert_pdfs_to_excel import convert_all_pdfs

# Page setup
st.set_page_config(page_title="PDF to Excel Converter", layout="centered")

# Title and description
st.title("📄 Mahindra Price List Converter")
st.write(
    """
    Upload one or more Mahindra price list PDFs below and convert them into a single Excel file.
    """
)

# Upload PDF files
uploaded_files = st.file_uploader(
    "📤 Upload PDF files",
    type="pdf",
    accept_multiple_files=True
)

# Directory to save PDFs
pdf_dir = "price-pdfs"

# Process uploaded files
if uploaded_files:
    os.makedirs(pdf_dir, exist_ok=True)

    # Save each file
    for file in uploaded_files:
        file_path = os.path.join(pdf_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

    st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully.")

    # Button to trigger conversion
    if st.button("🚀 Convert to Excel"):
        with st.spinner("Converting PDFs to Excel…"):
            try:
                excel_path = convert_all_pdfs(pdf_dir)
                if excel_path and os.path.exists(excel_path):
                    with open(excel_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Excel File",
                            data=f,
                            file_name=os.path.basename(excel_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("❌ Conversion failed. No valid pricing data found in the PDFs.")
            except Exception as e:
                st.error(f"❌ An error occurred during conversion:\n\n{e}")
