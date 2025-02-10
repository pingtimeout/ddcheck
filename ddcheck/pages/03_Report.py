import pandas as pd
import streamlit as st
from natsort import natsorted
from openai import OpenAI

from ddcheck.storage import DdcheckMetadata, InsightQualifier
from ddcheck.storage.list import get_uploaded_metadata
from ddcheck.storage.upload import write_metadata_to_disk


def create_chat_box() -> None:
    st.subheader("DDCheck Chat")

    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="foo",
    )

    # Initialize the chat history with the system prompt and the user prompt containing all the insights
    if "messages" not in st.session_state:
        system_prompt = (
            "You are a knowledgeable Software Engineer focusing on solving performance issues.  \n\n"
            "You are provided with a list of facts that were observed on a given server.  "
            "Your role is to help the user make sense out of these facts.  "
            "You may recommend the user to run additional Linux CLI tools to further refine your analysis.  "
            "Ensure that you only rely on standard Linux tools.\n\n"
            ""
            "The server you are analysing is running Dremio, a data lakehouse platform.  Dremio is written in Java but also contains native code run with JNI.\n\n"
            ""
            "The DCOTC is a proxy metric to quickly get an idea of where the biggest bottleneck in the system is.  "
            "It comes from the JPDM methodology.\n "
            "* When it is `System`, it means that the server is spending an abnormal amount of CPU time in kernel space, compared to the time spent in userspace.  The associated root cause issue usually is too many context switches (too many threads running), or too many small disk I/O operations, or too many network I/O operations.\n"
            "* When it is `User`, it means that most of the CPU time is spent in user space.  The associated root cause issue usually is a too high GC overhead or an algorithmic issue in the Java code itself.\n"
            "* When it is `None`, it means that something is preventing all CPUs from being fully utilized.  The associated root cause issue usually is too small thread pools, or a node that is not receiving enough workload."
        )
        initial_user_prompt = f"Narrow down the list of possible root causes for performance issues using the following facts for the node {selected_node}.\n"
        for q in [
            InsightQualifier.OK,
            InsightQualifier.INTERESTING,
            InsightQualifier.BAD,
        ]:
            initial_user_prompt += "".join(
                f"* {i.message}\n"
                for i in insights_per_qualifier_and_node.get(q, {}).get(
                    selected_node, []
                )
            )
        st.session_state.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_user_prompt},
        ]

    # Display chat messages from history on app rerun except the system prompt as it is too large
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Type anything to start the analysis"):
        # Add user message to chat history and display it in the chat message container
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-r1:8b",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})


st.set_page_config(layout="wide")

if "ddcheck_id" not in st.session_state:
    st.switch_page("pages/01_Upload.py")


metadata: DdcheckMetadata | None = get_uploaded_metadata(st.session_state.ddcheck_id)

if metadata is None:
    st.switch_page("pages/01_Upload.py")
else:
    with st.container():
        col1, col2 = st.columns([10, 2], vertical_alignment="bottom")
        with col1:
            st.title(f"Report for {metadata.original_filename}")
        with col2:
            if st.button("Rerun analysis", use_container_width=True):
                metadata.reset()
                write_metadata_to_disk(metadata)
                st.switch_page("pages/02_Analysis.py")

    insights_per_qualifier_and_node = metadata.insights_per_qualifier_and_node()
    insights_per_node_and_qualifier = metadata.insights_per_node_and_qualifier()

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
    st.markdown("### Node selection")
    selected_node = st.selectbox("Select a Dremio node", natsorted(metadata.nodes))

    # Display the insights for the selected node
    if selected_node:
        st.divider()
        st.write("### Insights")
        labels_per_qualifier = {
            InsightQualifier.BAD: ("🔴"),
            InsightQualifier.INTERESTING: ("🟡"),
            InsightQualifier.OK: ("🟢"),
            InsightQualifier.DEBUG: ("🔎"),
        }

        for qualifier in labels_per_qualifier:
            insights = insights_per_qualifier_and_node.get(qualifier, {}).get(
                selected_node, []
            )
            if len(insights) != 0:
                st.write(f"{labels_per_qualifier[qualifier]} **{qualifier.name}**")
                for insight in insights:
                    st.write(f"* {selected_node}: {insight.message}")

        st.divider()
        st.subheader("Metrics")

        if selected_node in metadata.cpu_usage:
            st.write("#### CPU usage")
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

        if selected_node in metadata.total_used_swap_mb:
            st.write("#### Swap usage")
            df = pd.DataFrame(metadata.total_used_swap_mb[selected_node])
            # Create a line chart with the Swap usage
            st.line_chart(
                df,
                # y="Swap used",
                use_container_width=True,
            )

        create_chat_box()
