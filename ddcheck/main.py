import streamlit as st
from st_pages import get_nav_from_toml, hide_pages

from ddcheck.utils.file_handling import get_all_metadata, save_uploaded_file

st.set_page_config(initial_sidebar_state="collapsed")

nav = get_nav_from_toml()
pg = st.navigation(nav)

st.title("DDCheck")
st.subheader("Dremio Diagnostics Tarball Analysis Tool")
st.write(
    "Upload a Dremio Diagnostics Tarball (.tar.gz) below. "
    "Only tarballs generated with Dremio Diagnostics Collector v3.3.1 or earlier are supported."
)
uploaded_file = st.file_uploader(
    "Choose a diagnostics tarball",
    type=["tar.gz", "gz", "application/gzip", "application/x-gzip"],
    help="Upload a Dremio diagnostics tarball (.tar.gz file)",
)

if uploaded_file is not None:
    # Save the uploaded file and switch to the analysis page
    file_path = save_uploaded_file(uploaded_file)
    st.success(f"File uploaded successfully to {file_path}")
    st.session_state.uploaded_file_path = str(file_path)
    st.switch_page("pages/analysis.py")

# Separator between upload and selection
st.divider()
st.write("Or select a previously uploaded tarball:")

# Previously uploaded tarballs section
existing_tarballs = get_all_metadata()
if existing_tarballs:
    # Create a list of dictionaries for the table
    table_data = [
        {
            "Original Filename": metadata.original_filename,
            "Upload Time (UTC)": metadata.upload_time.isoformat(),
            "DDCheck ID": metadata.ddcheck_id,
        }
        for metadata in existing_tarballs
    ]

    selected_row = st.data_editor(
        table_data,
        column_config={
            "Original Filename": st.column_config.TextColumn("Original Filename"),
            "Upload Time (UTC)": st.column_config.TextColumn("Upload Time (UTC)"),
            "DDCheck ID": st.column_config.TextColumn("DDCheck ID"),
        },
        hide_index=True,
        num_rows="fixed",
    )

    # If a row is selected (clicked)
    if selected_row is not None:
        selected_id = None
        for row in table_data:
            if row == selected_row:
                selected_id = row["DDCheckID"]
                break

        if selected_id:
            for metadata in existing_tarballs:
                if metadata.ddcheck_id == selected_id:
                    st.session_state.uploaded_file_path = metadata.extract_path
                    st.switch_page("pages/analysis.py")
else:
    st.info("No previously uploaded tarballs found")

hide_pages(["Analysis"])
