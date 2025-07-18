import streamlit as st
from github import Github
from io import BytesIO

def get_github_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["GITHUB_REPO"]
    return Github(token).get_repo(repo_name)

def get_github_branch():
    return st.secrets.get("GITHUB_BRANCH", "main")

def download_file_from_repo(repo, path):
    file_content = repo.get_contents(path, ref=get_github_branch())
    return BytesIO(file_content.decoded_content), file_content.sha

def upload_or_update_file(repo, path, file_bytes, commit_message):
    file_bytes.seek(0)
    content = file_bytes.read()

    try:
        existing = repo.get_contents(path, ref=get_github_branch())
        repo.update_file(existing.path, commit_message, content, existing.sha, branch=get_github_branch())
    except:
        repo.create_file(path, commit_message, content, branch=get_github_branch())
