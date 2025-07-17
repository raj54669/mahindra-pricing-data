import streamlit as st
import os
from convert_pdfs_to_excel import convert_all_pdfs

st.set_page_config(page_title="PDF to Excel Converter", layout="centered")

st.title("📄 Mahindra Price List Converter")
st.write("Upload PDF files to generate an Excel master sheet.")

uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    os.makedirs("price-pdfs", exist_ok=True)
    
    for file in uploaded_files:
        with open(os.path.join("price-pdfs", file.name), "wb") as f:
            f.write(file.getbuffer())

    st.success("✅ Files uploaded successfully")

    if st.button("Convert to Excel"):
        excel_path = convert_all_pdfs()
        if excel_path:
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📥 Download Excel File",
                    data=f,
                    file_name=os.path.basename(excel_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("❌ Conversion failed. Check PDF formats.")
