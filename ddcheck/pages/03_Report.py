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
    st.write(metadata.ddcheck_id)

    # Add a button to rerun the analysis
    if st.button("Rerun analysis"):
        metadata.reset()
        write_metadata_to_disk(metadata)
        st.switch_page("pages/02_Analysis.py")

    insights_per_qualifier_and_node = metadata.insights_per_qualifier_and_node()

    # Display all the checks that were performed
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

    # Show a selector with all the nodes
    selected_node = st.selectbox("Select a node", metadata.nodes)

    # Display the insights for the selected node
    if selected_node:
        st.write("### Node-specific insights")
        labels_per_qualifier = {
            InsightQualifier.BAD: ("🔴"),
            InsightQualifier.INTERESTING: ("🟡"),
            InsightQualifier.OK: ("🟢"),
        }

        for qualifier in labels_per_qualifier:
            insights = insights_per_qualifier_and_node.get(qualifier, {}).get(
                selected_node, []
            )
            if len(insights) != 0:
                st.write(f"{labels_per_qualifier[qualifier]} **{qualifier.name}**")
                for insight in insights:
                    st.write(f"* {selected_node}: {insight.message}")
            else:
                st.write(f"* {selected_node}: No insight")

        st.subheader("Node-specific metrics")
        st.write("#### CPU usage")

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
