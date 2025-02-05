import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


def redirect_to_upload():
    ctx = get_script_run_ctx()
    if ctx is not None:
        st.switch_page("pages/01_Upload.py")


if "uploaded_file_path" not in st.session_state:
    st.warning("Please upload a diagnostics file first")
    redirect_to_upload()
    st.stop()

st.title("DDCheck")
st.subheader("Dremio Diagnostics Tarball Analysis Tool")

# Add your analysis logic here
st.write(f"Analyzing file: {st.session_state.uploaded_file_path}")

# Show both pages in navigation when we're on analysis page
# st.sidebar.page_link("pages/01_Upload.py", label="Upload")
# st.sidebar.page_link("pages/_Analysis.py", label="Analysis")
