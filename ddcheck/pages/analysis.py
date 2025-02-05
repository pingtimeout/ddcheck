import streamlit as st

if st.query_params["ddcheck_id"]:
    st.session_state["ddcheck_id"] = st.query_params["ddcheck_id"]

# Add your analysis logic here
st.write(f"Analyzing file: {st.session_state.ddcheck_id}")
