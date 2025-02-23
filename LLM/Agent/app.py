import logging
import sys

import streamlit as st

from pages import init_streamlit
from pages.components.sidebar import render_sidebar
from pages.components.history import show_conversation_history
from pages.components.chat import chat_with_conversation, build_system_prompt_with_memory, execute_action

# 设置页面为宽页模式
st.set_page_config(layout="wide")

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # logging.FileHandler('app.log')
    ]
)

init_streamlit()

# 页面标题
st.title("Retail Assistant Chat")
st.subheader("Requirement, Research, Plan, Execute")
st.markdown("---")

# 侧边栏：记忆管理
with st.sidebar:
    render_sidebar()

show_conversation_history()

# 处理用户输入
col1, col2 = st.columns([0.2, 0.8])
trigger_str, system_prompt = "", ""

with col1:
    triggers = st.multiselect("Select Triggers", st.session_state.memory_manager.triggers)
with col2:
    # 增加选择的触发词到预览
    if triggers:
        trigger_str = '\n'.join([f"`{t}`" for t in triggers])
    
    system_prompt = build_system_prompt_with_memory(trigger_str, "")
    # Because I need know the memory details, so It must write it out
    st.write(system_prompt)

if prompt := st.chat_input("Type something..."):
    response = chat_with_conversation(trigger_str + prompt, system_prompt, st.session_state.quoted_history)
    
    if "run_plan" in response.lower():
        response = execute_action(response, {})
