import os
import uuid
from pathlib import Path
import streamlit as st

def save_uploaded_file(uploaded_file):
    # Create uploads directory if it doesn't exist
    upload_dir = Path("/tmp/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a random filename with original extension
    random_filename = f"{uuid.uuid4()}.tar.gz"
    file_path = upload_dir / random_filename
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def main():
    st.title("DDCheck")
    
    st.write(
        "Upload a Dremio Diagnostics Tarball (.tar.gz) below. "
        "Only tarballs generated with Dremio Diagnostics Collector v3.3.1 or earlier are supported."
    )
    
    uploaded_file = st.file_uploader(
        "Choose a diagnostics tarball",
        type=["tar.gz"],
        help="Upload a Dremio diagnostics tarball (.tar.gz file)",
    )
    
    if uploaded_file is not None:
        file_path = save_uploaded_file(uploaded_file)
        st.success(f"File uploaded successfully")

if __name__ == "__main__":
    main()
