import logging
import streamlit as st
from .reflect import reflect_on_conversation

@st.dialog("Select Session")
def select_session_dialog():
    session_name = st.selectbox("Select Session", ["New Session"] + [s["session_name"] for s in st.session_state.session_manager.list()])
    if st.button("Select"):
        if session_name == "New Session":
            st.session_state.session = st.session_state.session_manager.new({"session_name": "New Session"})
        else:
            st.session_state.session = st.session_state.session_manager.get({"session_name": session_name})
        st.rerun()

def render_sidebar():
    st.header("Session Management")
    if st.button("Select Session"):
        select_session_dialog()
    
    st.header("Reflect on Conversation")
    if prompt := st.chat_input("Something should be reflected on..."):
        try:
            reflection = reflect_on_conversation(st.session_state.quoted_history, prompt)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error(f"Reflection error: {str(e)}", exc_info=True)