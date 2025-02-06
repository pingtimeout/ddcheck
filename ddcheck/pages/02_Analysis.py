import streamlit as st

from ddcheck.analysis.ttop import analyse_top_output
from ddcheck.utils.upload import get_uploaded_metadata

if "ddcheck_id" in st.query_params:
    st.session_state["ddcheck_id"] = st.query_params["ddcheck_id"]

if "ddcheck_id" not in st.session_state:
    st.switch_page("pages/01_Upload.py")

# Add your analysis logic here
metadata = get_uploaded_metadata(st.session_state.ddcheck_id)
st.write(f"Analysis for {metadata.original_filename} (ID: {metadata.ddcheck_id})")

# Invoke the ttop analysis function and write its result
for node in metadata.nodes:
    st.write(node)
    st.write(analyse_top_output(metadata, node))
