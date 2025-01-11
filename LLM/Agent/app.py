import re
import logging
import sys
import json
import traceback
import streamlit as st
from openai import OpenAI
from datetime import datetime
import os
import pyperclip
from dotenv import load_dotenv
from typing import List, Dict
from memory import MemoryManager, Memory, add_memory_dialog, show_memory_dialog

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

# 设置页面为宽页模式
st.set_page_config(layout="wide")

# 加载环境变量
load_dotenv()

# 初始化 OpenAI Chat 客户端
chat_client = OpenAI(
    base_url=os.getenv("CHAT_BASE_URL"),
    api_key=os.getenv("CHAT_API_KEY")
)

# 初始化记忆管理器
if 'memory_manager' not in st.session_state:
    st.session_state.memory_manager = MemoryManager()
# 初始化对话历史
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
    st.session_state.quoted_history = []
    st.session_state.quoted_ids = set()  # 用于跟踪已引用的对话ID

def clear_quotes():
    for key in st.session_state.keys():
        if key.startswith("quote_"):
            st.session_state[key] = False
    
    st.session_state.quoted_history = []
    st.session_state.quoted_ids = set()

def get_relevant_memories(query: str) -> List[Memory]:
    """获取与查询相关的记忆
    
    Args:
        query: 查询内容
        search_type: 搜索类型，可选 "vector"（向量搜索）、"keyword"（关键词搜索）、"trigger"（触发器搜索）
        exact_match: 是否精确匹配（仅对关键词搜索有效）
        
    Returns:
        相关的记忆列表
    """
    memory_manager = st.session_state.get('memory_manager')
    if not memory_manager:
        memory_manager = MemoryManager()
        st.session_state.memory_manager = memory_manager
    
    relevant_memories = []
    for trigger in memory_manager.triggers:
        # 输入里有 trigger 词，直接匹配
        if trigger in query:
            relevant_memories.extend(memory_manager.search_memory(query=trigger, search_type="trigger"))
    
    return relevant_memories

def reflect_on_conversation(conversation_history: List[Dict]) -> str:
    """对话反思，分析用户特征和习惯"""
    prompt = """从以下对话中提取关键信息，重点关注用户(user)的表述。特别注意以下两点：
1. 用户的积极反馈，例如称赞、认可等，表明助手(assistant)的回答效果良好，要记录下来。
2. 用户的消极反馈，例如质疑、不满等，需要记住犯错的地方。

请提供以下方面的分析：
1. 用户的兴趣爱好
2. 重要的个人信息
3. 交谈习惯和说话方式
4. 值得记住的具体事件或信息

对输出结果进行结构化表示，格式如下：
```json
[
{{
     "summary": xx, //关键总结
     "labels": ['xx', 'xxx'], // 相关标签
     "trigger": 'xxx' // 触发词，可以包含 _ 拼接多个单词，但不能有空格
}}, ... // 其他的总结信息
]
```

对话历史如下：
{conversations}
"""
    try:
        logging.info(f"Starting reflection on {len(conversation_history)} conversation items")
        reflection_stream = chat_client.chat.completions.create(
            model=os.getenv("CHAT_MODEL"),
            messages=[
                {"role": "system", "content": "你是一个专注于分析和总结的AI助手。"},
                {"role": "user", "content": prompt.format(conversations="\n".join([f"{c['role']} - {c['content']}" for c in conversation_history]))},
            ],
            stream=True,
        )
        print(reflection_stream)
        reflection = st.write_stream(reflection_stream)
        
        # 保存反思结果到记忆
        mem_json = json.loads(re.match(r"```json\n(.*)\n```", reflection, re.DOTALL).group(1))
        memory_manager = st.session_state.get('memory_manager')
        if memory_manager:
            for mem in mem_json:
                mem["labels"] = mem["labels"] + ["reflection"]
                memory_manager.add_memory(**mem)
        
        clear_quotes()
        return reflection
    except Exception as e:
        logging.error(traceback.format_exc())
        return f"反思过程出现错误: {str(e)}"

def chat_with_memory_and_history(user_input: str) -> str:
    """与用户对话，包含记忆上下文"""
    # 获取相关记忆，自动选择最佳搜索方式
    relevant_memories = get_relevant_memories(user_input)
    
    # 构建记忆上下文
    memory_context = "相关的用户信息：\n"
    for memory in relevant_memories:
        memory_context += f"- [{memory.created_at}] {memory.summary}\n"
    
    system_prompt = f"""你是一个友好的AI助手，请参考以下用户相关信息：
{memory_context}
在回答时，适当地运用这些信息来个性化对话。"""
    
    # 添加用户消息
    with st.chat_message("user"):
        with st.expander("System Prompt"):
            st.write(system_prompt)
        st.write(user_input)
    
    messages = [{"role": "system", "content": system_prompt}] + \
        [{"role": m["role"], "content": m["content"]} for m in st.session_state.quoted_history] + \
        [{"role": "user", "content": user_input}]
    
    # 记录对话历史
    st.session_state.conversation_history.append({
        "role": "user",
        "time": str(datetime.now()),
        "content": user_input,
        "id": str(datetime.now().timestamp())
    })

    # 生成并显示AI回复
    with st.chat_message("assistant"):
        stream = chat_client.chat.completions.create(
            model=os.getenv("CHAT_MODEL"),
            messages=messages,
            stream=True,
        )
        response = st.write_stream(stream)
    
    # 添加AI回复到消息记录
    st.session_state.conversation_history.append({
        "role": "assistant",
        "time": str(datetime.now()),
        "content": response,
        "id": str(datetime.now().timestamp())
    })
    
    # 增加工具调用选项，依赖 LM 返回结果

    # 清空被引用的对话历史
    clear_quotes()

# 页面标题
st.title("Retail Assistant Chat")

# 侧边栏：记忆管理
with st.sidebar:
    st.header("Memory Management")

    # 创建新记忆
    st.subheader("Create New Memory")
    if st.button("Add Memory"):
        add_memory_dialog()

    # 列出现有记忆
    st.subheader("Select Memories")
    if st.button("Show Memory"):
        show_memory_dialog()

    st.header("Reflect on Conversation")
    if st.button("Reflect"):
        try:
            reflection = reflect_on_conversation(st.session_state.quoted_history)
            st.write(reflection)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error(f"Reflection error: {str(e)}", exc_info=True)
    else:
        st.warning("No conversation history to reflect on.")

# 显示历史消息，按问答对分组
for i in range(0, len(st.session_state.conversation_history), 2):
    if i+1 >= len(st.session_state.conversation_history):
        break
        
    user_msg = st.session_state.conversation_history[i]
    assistant_msg = st.session_state.conversation_history[i+1]
    
    # 显示问答对
    with st.container():
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            with st.chat_message(user_msg["role"]):
                st.markdown(user_msg["content"])
            with st.chat_message(assistant_msg["role"]):
                st.markdown(assistant_msg["content"])
        with col2:
            if st.checkbox("Quote", key=f"quote_{i}"):
                # 检查是否已经引用过
                if user_msg["id"] not in st.session_state.quoted_ids:
                    # 拼接被引用的对话历史
                    st.session_state.quoted_history.extend([user_msg, assistant_msg])
                    st.session_state.quoted_ids.add(user_msg["id"])
            # Copy buttons
            if st.button("Copy User Message", key=f"copy_user_{i}"):
                pyperclip.copy(user_msg["content"])  # Copy to clipboard
                st.success("User message copied to clipboard!")

            if st.button("Copy Assistant Message", key=f"copy_assistant_{i}"):
                pyperclip.copy(assistant_msg["content"])  # Copy to clipboard
                st.success("Assistant message copied to clipboard!")

# 处理用户输入
if prompt := st.chat_input("Type something..."):
    mem_str = chat_with_memory_and_history(prompt)
