import pandas as pd
import streamlit as st
from natsort import natsorted

from ddcheck.storage import DdcheckMetadata, InsightQualifier
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
        metadata.reset()
        write_metadata_to_disk(metadata)
        st.switch_page("pages/02_Analysis.py")

    st.subheader("Insights")
    insights_per_qualifier_and_node = metadata.insights_per_qualifier_and_node()
    labels_per_qualifier = {
        InsightQualifier.BAD: ("🔴"),
        InsightQualifier.INTERESTING: ("🟡"),
        InsightQualifier.OK: ("🟢"),
    }

    total_checks = sum(
        len(insights)
        for insights in insights_per_qualifier_and_node[InsightQualifier.CHECK].values()
    )
    with st.status(
        f"📋 {total_checks} checks performed",
        expanded=False,
    ) as status:
        for node_and_insights in natsorted(
            insights_per_qualifier_and_node[InsightQualifier.CHECK].items()
        ):
            for insight in node_and_insights[1]:
                status.write(f"{node_and_insights[0]}: {insight.message}")

    total_insights = 0
    for qualifier in labels_per_qualifier:
        insights_per_node = insights_per_qualifier_and_node.get(qualifier, {})
        # Count the insights across all nodes
        total_qualified_insights = sum(
            len(insights) for insights in insights_per_node.values()
        )
        total_insights += total_qualified_insights
        if total_qualified_insights != 0:
            st.write(f"{labels_per_qualifier[qualifier]} **{qualifier.name}**")
            nodes = insights_per_node.items()
            for node, insights in natsorted(nodes):
                for insight in insights:
                    st.write(f"* {node}: {insight.message}")

    if total_insights == 0:
        st.write("No insights found")

    st.subheader("Per-node metrics")

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
