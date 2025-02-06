import pandas as pd
import streamlit as st

from ddcheck.storage import DdcheckMetadata
from ddcheck.storage.list import get_uploaded_metadata

st.set_page_config(layout="wide")

# Define CPU metrics display order and colors (bottom to top)
CPU_METRICS = [
    ("hi", "#FF9F1C"),  # hardware interrupts - orange
    ("si", "#6C5B7B"),  # software interrupts - purple
    ("st", "#C8C8C8"),  # stolen - gray
    ("us", "#4ECDC4"),  # user - cyan
    ("ni", "#45B7D1"),  # user nice - light blue
    ("sy", "#FFD93D"),  # system - yellow
    ("wa", "#FF6B6B"),  # iowait - red
    ("id", "#96CEB4"),  # idle - soft green
]

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

    # Invoke the ttop analysis function and write its result
    for node in metadata.nodes:
        st.subheader(f"Node: {node}")

        if node in metadata.cpu_usage:
            cpu_data = metadata.cpu_usage[node]
            if any(cpu_data.values()):
                # Create DataFrame for plotting
                df = pd.DataFrame(cpu_data)

                # Create stacked area chart
                st.area_chart(
                    df[list(metric for metric, _ in CPU_METRICS)],
                    color=list(color for _, color in CPU_METRICS),
                )
            else:
                st.warning("No CPU data available for this node")
