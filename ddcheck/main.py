import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/01_Upload.py", title="Upload", icon="📤"),
        st.Page("pages/02_Analysis.py", title="Analysis", icon="🔍"),
        st.Page("pages/03_Report.py", title="Report", icon="📊"),
    ]
)
pg.run()
