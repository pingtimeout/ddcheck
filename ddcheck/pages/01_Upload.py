import streamlit as st
from streamlit.column_config import LinkColumn

from ddcheck.storage.list import list_all_uploaded_tarballs
from ddcheck.storage.upload import save_uploaded_tarball

st.set_page_config(layout="centered")

st.title("DDCheck")
st.subheader("Dremio Diagnostics Tarball Analysis Tool")
st.write(
    "Upload a Dremio Diagnostics Tarball (.tar.gz) below. "
    "Only tarballs generated with Dremio Diagnostics Collector v3.3.1 or earlier are supported."
)

uploaded_file = st.file_uploader(
    "Choose a diagnostics tarball",
    type=["gz", "tgz"],
    help="Upload a Dremio diagnostics tarball (.tar.gz file)",
)

if uploaded_file is not None:
    # Save the uploaded file and switch to the analysis page
    metadata = save_uploaded_tarball(uploaded_file)
    if metadata is None:
        st.error(
            "Invalid tarball uploaded. Please upload a valid Dremio diagnostics tarball."
        )
    else:
        st.success(f"File uploaded successfully as {metadata.ddcheck_id}")
        st.session_state["ddcheck_id"] = metadata.ddcheck_id
        st.switch_page("pages/02_Analysis.py")

# Separator between upload and selection
st.divider()
st.write("Or select a previously uploaded tarball:")

# Previously uploaded tarballs section
existing_tarballs = list_all_uploaded_tarballs()
if existing_tarballs:
    # Sort the table data before displaying it by upload time (newest first)
    table_data = sorted(
        [
            {
                "DDCheck ID": f"Analysis?ddcheck_id={metadata.ddcheck_id}",
                "Original Filename": metadata.original_filename,
                "Upload Time (UTC)": metadata.upload_time.isoformat(),
            }
            for metadata in existing_tarballs
        ],
        key=lambda x: x["Upload Time (UTC)"],
        reverse=True,
    )

    # Create a dataframe for the table
    st.dataframe(
        table_data,
        hide_index=True,
        use_container_width=True,
        column_config={
            "DDCheck ID": LinkColumn(
                "DDCheck ID",
                display_text=r".*ddcheck_id=(.*)",
            )
        },
    )

else:
    st.info("No previously uploaded tarballs found")
