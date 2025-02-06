import pandas as pd
import streamlit as st

from ddcheck.analysis.top import analyse_top_output
from ddcheck.storage import DdcheckMetadata
from ddcheck.storage.list import get_uploaded_metadata

# Each node is associated to a dict containing a list of values for keys us, ni

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

if "ddcheck_id" in st.query_params:
    st.session_state["ddcheck_id"] = st.query_params["ddcheck_id"]

if "ddcheck_id" not in st.session_state:
    st.switch_page("pages/01_Upload.py")

# Add your analysis logic here
metadata: DdcheckMetadata | None = get_uploaded_metadata(st.session_state.ddcheck_id)
if metadata is None:
    st.switch_page("pages/01_Upload.py")
else:
    st.write(f"Analysis for {metadata.original_filename} (ID: {metadata.ddcheck_id})")

    # Invoke the ttop analysis function and write its result
    for node in metadata.nodes:
        st.subheader(f"Node: {node}")

        # Show analysis state
        analysis_state = metadata.analysis_state.get(node, "not_started")
        if analysis_state == "not_started":
            st.write("Analyzing CPU data for this node...")
            analyse_top_output(metadata, node)
        elif analysis_state == "in_progress":
            st.write("Analysis in progress...")
        elif analysis_state == "failed":
            st.error("Analysis failed for this node")
            continue

        # Analyze node data if not already analyzed
        if metadata.cpu_usage == {} or node not in metadata.cpu_usage:
            st.write("Analyzing CPU data for this node...")
            analyse_top_output(metadata, node)

        if analysis_state == "completed" and node in metadata.cpu_usage:
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
