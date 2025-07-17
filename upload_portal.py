import streamlit as st
import os
from convert_pdfs_to_excel import convert_all_pdfs

# Streamlit page config
st.set_page_config(page_title="PDF to Excel Converter", layout="centered")

# Title and instructions
st.title("📄 Mahindra Price List Converter")
st.write("Upload PDF files to generate an Excel master sheet.")

# Upload section
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type="pdf",
    accept_multiple_files=True
)

# Handle uploaded files
if uploaded_files:
    os.makedirs("price-pdfs", exist_ok=True)

    # Save PDFs to folder
    for file in uploaded_files:
        save_path = os.path.join("price-pdfs", file.name)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())

    st.success("✅ Files uploaded successfully")

    # Button to trigger conversion
    if st.button("Convert to Excel"):
        try:
            excel_path = convert_all_pdfs("price-pdfs")
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
            st.error(f"❌ Conversion failed due to an error: {e}")
