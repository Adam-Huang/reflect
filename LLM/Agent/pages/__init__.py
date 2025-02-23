from dotenv import load_dotenv
import streamlit as st
from core.session_manager import LocalSessionManager as SessionManager

# 加载环境变量
load_dotenv()

def init_streamlit():
    # 初始化对话管理
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
        if len(st.session_state.session_manager.list()) < 1:
            st.session_state.session_manager.new({})

    if 'session' not in st.session_state:
        session_info = st.session_state.session_manager.list()[0]
        st.session_state.session = st.session_state.session_manager.get(session_info)

    if 'quoted_history' not in st.session_state:
        st.session_state.quoted_history = []
        st.session_state.quoted_ids = set()  # 用于跟踪已引用的对话ID

    if "quotes" not in st.session_state:
        st.session_state.quotes = {}