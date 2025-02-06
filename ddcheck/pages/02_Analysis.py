import streamlit as st

from ddcheck.analysis.top import analyse_top_output
from ddcheck.storage import DdcheckMetadata
from ddcheck.storage.list import get_uploaded_metadata

st.set_page_config(layout="centered")

if "ddcheck_id" in st.query_params:
    st.session_state["ddcheck_id"] = st.query_params["ddcheck_id"]

if "ddcheck_id" not in st.session_state:
    st.switch_page("pages/01_Upload.py")

metadata: DdcheckMetadata | None = get_uploaded_metadata(st.session_state.ddcheck_id)
if metadata is None:
    st.switch_page("pages/01_Upload.py")
else:
    with st.status(
        f"Analysing {metadata.original_filename} (ID: {metadata.ddcheck_id})...",
        expanded=True,
    ) as status:
        # Invoke the ttop analysis function for each node
        for node in metadata.nodes:
            if node not in metadata.cpu_usage:
                with st.empty():
                    st.write(f"Analysing ttop output for {node}...")
                    st.write(
                        f"Result of ttop output analysis for {node}: {analyse_top_output(metadata, node)}"
                    )
            else:
                st.write(f"Skipping analysis for {node} - already completed")
        status.update(label="Analysis complete", state="complete")
        st.switch_page("pages/03_Report.py")
