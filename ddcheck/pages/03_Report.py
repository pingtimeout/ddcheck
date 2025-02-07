import pandas as pd
import streamlit as st

from ddcheck.storage import AnalysisState, DdcheckMetadata
from ddcheck.storage.list import get_uploaded_metadata
from ddcheck.storage.upload import write_metadata_to_disk

st.set_page_config(layout="wide")

if "ddcheck_id" not in st.session_state:
    st.switch_page("pages/01_Upload.py")

# Add your analysis logic here
metadata: DdcheckMetadata | None = get_uploaded_metadata(st.session_state.ddcheck_id)
if metadata is None:
    st.switch_page("pages/01_Upload.py")
else:
    st.title(f"Report for {metadata.original_filename}")

    # Add a button to rerun the analysis
    if st.button("Rerun analysis"):
        metadata.analysis_state = {
            node: {
                state: AnalysisState.NOT_STARTED
                for state in metadata.analysis_state[node]
            }
            for node in metadata.nodes
        }
        write_metadata_to_disk(metadata)
        st.switch_page("pages/02_Analysis.py")

    # Show a selector with all the nodes
    selected_node = st.selectbox("Select a node", metadata.nodes)

    if selected_node:
        st.subheader("CPU usage")

        if selected_node in metadata.cpu_usage:
            df = pd.DataFrame(metadata.cpu_usage[selected_node])
            df.rename(
                columns={
                    "us": "User",
                    "sy": "System",
                    "id": "Idle",
                    "wa": "I/O Wait",
                },
                inplace=True,
            )
            df["Total"] = 100 - df["Idle"]
            # Create a line chart with the CPU usage computed as 100 - idle.  Idle CPU usage is displayed with a green line.
            st.line_chart(
                df,
                y=["Total", "User", "System", "I/O Wait"],
                use_container_width=True,
                color=["#7f7f7f", "#1f77b4", "#d62728", "#ff7f0e"],
            )
            # st.line_chart(df[["Total", "User", "System", "I/O Wait"]], use_container_width=True, color=["#7f7f7f", "#1f77b4", "#d62728", "#ff7f0e"])
