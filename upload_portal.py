import streamlit as st
from github import Github

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["GITHUB_REPO"]
BRANCH = st.secrets["GITHUB_BRANCH"]
UPLOAD_PATH = st.secrets["PDF_UPLOAD_PATH"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

st.set_page_config(page_title="PDF Uploader", layout="centered")
st.title("📤 Upload Price List PDF to GitHub")
st.caption("Upload model-wise price list PDF files. They'll automatically update the pricing viewer.")

uploaded_file = st.file_uploader("Select a Price List PDF", type="pdf")

if uploaded_file:
    file_bytes = uploaded_file.read()
    file_name = uploaded_file.name
    file_path = f"{UPLOAD_PATH}{file_name}"

    try:
        existing = repo.get_contents(file_path, ref=BRANCH)
        repo.update_file(
            path=file_path,
            message=f"Updated {file_name} via Streamlit",
            content=file_bytes,
            sha=existing.sha,
            branch=BRANCH
        )
        st.success(f"✅ File '{file_name}' updated successfully.")
    except:
        repo.create_file(
            path=file_path,
            message=f"Added {file_name} via Streamlit",
            content=file_bytes,
            branch=BRANCH
        )
        st.success(f"✅ File '{file_name}' uploaded successfully.")
