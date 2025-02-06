import streamlit as st

if "ddcheck_id" in st.query_params:
    st.session_state["ddcheck_id"] = st.query_params["ddcheck_id"]

if not "ddcheck_id" in st.session_state:
    st.switch_page("pages/01_Upload.py")

# Add your analysis logic here
st.write(f"Analyzing file: {st.session_state.ddcheck_id}")
