import logging
import sys

import streamlit as st

from core.memory import MemoryManager
from pages.components.sidebar import render_sidebar
from pages.components.history import show_conversation_history
from pages.components.chat import chat_with_memory_and_history, build_system_prompt_with_memory, do_workflow

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

# 初始化记忆管理器
if 'memory_manager' not in st.session_state:
    st.session_state.memory_manager = MemoryManager()

# 页面标题
st.title("Retail Assistant Chat")

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
    
    system_prompt, workflow_name = build_system_prompt_with_memory(trigger_str, {})
    # Because I need know the memory details, so It must write it out
    st.write(system_prompt)

if prompt := st.chat_input("Type something..."):
    response = chat_with_memory_and_history(trigger_str + prompt, system_prompt)
    
    if workflow_name != "":
        logging.warning(f"This is {workflow_name} workflow. Please follow the instructions.")
        response = do_workflow(response)
        logging.info(f"Workflow {workflow_name} completed.")
