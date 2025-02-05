import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


def main():
    st.set_page_config(page_title="DDCheck", initial_sidebar_state="collapsed")
    ctx = get_script_run_ctx()
    if ctx is not None:
        st.switch_page("pages/upload.py")


if __name__ == "__main__":
    main()
