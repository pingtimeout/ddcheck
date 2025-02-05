import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


def redirect_to_upload():
    ctx = get_script_run_ctx()
    if ctx is not None:
        st.switch_page("pages/upload.py")


def show():
    st.title("DDCheck")
    st.subheader("Dremio Diagnostics Tarball Analysis Tool")
    st.header("Analysis")

    if "uploaded_file_path" not in st.session_state:
        st.warning("Please upload a diagnostics file first")
        redirect_to_upload()
        return

    # Add your analysis logic here
    st.write(f"Analyzing file: {st.session_state.uploaded_file_path}")

    # Show both pages in navigation when we're on analysis page
    st.sidebar.page_link("pages/upload.py", label="Upload")
    st.sidebar.page_link("pages/_analysis.py", label="Analysis")
