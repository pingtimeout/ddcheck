import streamlit as st

if "ddcheck_id" in st.query_params:
    st.session_state["ddcheck_id"] = st.query_params["ddcheck_id"]

# Add your analysis logic here
st.write(f"Analyzing file: {st.session_state.ddcheck_id}")
