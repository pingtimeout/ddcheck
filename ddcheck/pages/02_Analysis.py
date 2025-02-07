import time

import streamlit as st

from ddcheck.analysis.analysis import analyse_tarball
from ddcheck.storage import AnalysisState, DdcheckMetadata
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
        # Invoke the ttop analysis function for each node if it has not been analysed yet
        for node, states in metadata.analysis_state.items():
            # if any of the states is COMPLETE, skip the node
            if AnalysisState.COMPLETED in states.values():
                st.write(f"Skipping analysis for {node} - already completed")
            else:
                with st.empty():
                    st.write(f"Analysing node {node}...")
                    analysis_output = analyse_tarball(metadata, node).name.lower()
                    time.sleep(0.1)
                    st.write(f"Analysis of node {node}: {analysis_output}")
        status.update(label="Analysis complete", state="complete")
        st.switch_page("pages/03_Report.py")
