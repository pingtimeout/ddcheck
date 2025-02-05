import streamlit as st

from ddcheck.utils.file_handling import save_uploaded_file


def show():
    st.title("DDCheck")
    st.subheader("Dremio Diagnostics Tarball Analysis Tool")
    st.header("Upload Diagnostics")
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
        st.success(f"File uploaded successfully to {file_path}")
        # Store the file path in session state for other pages to access
        st.session_state.uploaded_file_path = str(file_path)
        # Show the Analysis link in sidebar
        st.sidebar.page_link("pages/_analysis.py", label="Analysis")
        # Redirect to analysis page
        st.switch_page("pages/_analysis.py")
