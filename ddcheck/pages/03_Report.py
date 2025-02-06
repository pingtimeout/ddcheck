import pandas as pd
import streamlit as st

from ddcheck.storage import DdcheckMetadata
from ddcheck.storage.list import get_uploaded_metadata

st.set_page_config(layout="wide")

if "ddcheck_id" not in st.session_state:
    st.switch_page("pages/01_Upload.py")

# Add your analysis logic here
metadata: DdcheckMetadata | None = get_uploaded_metadata(st.session_state.ddcheck_id)
if metadata is None:
    st.switch_page("pages/01_Upload.py")
else:
    # if any of the analysis states is not completed, we redirect to the upload page
    if any(state != "completed" for state in metadata.analysis_state.values()):
        st.error("Analysis not completed for all nodes. Redirecting to upload page...")
        st.session_state.pop("ddcheck_id")
        st.switch_page("pages/01_Upload.py")

    st.title(f"Report for {metadata.original_filename}")

    # Show a selector with all the nodes
    selected_node = st.selectbox("Select a node", metadata.nodes)

    if selected_node:
        st.subheader("CPU usage")

        if selected_node in metadata.cpu_usage:
            df = pd.DataFrame(metadata.cpu_usage[selected_node])

            # Create a line chart with the CPU usage computed as 100 - idle.  Idle CPU usage is displayed with a green line.
            df["Total"] = 100 - df["id"]
            st.line_chart(df["Total"], use_container_width=True, color="#1f77b4")
