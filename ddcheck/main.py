import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/01_Upload.py", title="Upload", icon="📤"),
        st.Page("pages/analysis.py", title="Analysis", icon="🔍"),
    ]
)
pg.run()
