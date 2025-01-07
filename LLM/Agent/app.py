import streamlit as st
import openai
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List, Dict
from .memory import MemoryManager

# 初始化 OpenAI Chat 客户端
chat_client = openai.OpenAI(
    base_url=os.getenv("CHAT_BASE_URL"),
    api_key=os.getenv("CHAT_API_KEY")
)

# 加载环境变量
load_dotenv()

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'memory' not in st.session_state:
    st.session_state.memory = {}
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'memory_index' not in st.session_state:
    st.session_state.memory_index = None
if 'memory_data' not in st.session_state:
    st.session_state.memory_data = []


def get_relevant_memories(query: str) -> List[Dict]:
    """获取与查询相关的记忆"""
    memory_manager = st.session_state.get('memory_manager')
    if not memory_manager:
        memory_manager = MemoryManager()
        st.session_state.memory_manager = memory_manager
    
    return memory_manager.search_memory(query)

def reflect_on_conversation(conversation_history: List[Dict]) -> str:
    """对话反思，分析用户特征和习惯"""
    reflection_prompt = f"""
    基于以下对话历史，请分析用户的特征、习惯和重要信息：
    {conversation_history}
    
    请提供以下方面的分析：
    1. 用户的兴趣爱好
    2. 重要的个人信息
    3. 交谈习惯和说话方式
    4. 值得记住的具体事件或信息
    """
    
    try:
        response = chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专注于分析和总结的AI助手。"},
                {"role": "user", "content": reflection_prompt}
            ]
        )
        reflection = response.choices[0].message['content']
        
        # 保存反思结果到记忆
        memory_manager = st.session_state.get('memory_manager')
        if memory_manager:
            memory_manager.add_memory(
                memory_text=reflection,
                summary='reflection',
                labels=['reflection']
            )
        
        return reflection
    except Exception as e:
        return f"反思过程出现错误: {str(e)}"

def chat_with_memory(user_input: str) -> str:
    """与用户对话，包含记忆上下文"""
    # 获取相关记忆
    relevant_memories = get_relevant_memories(user_input)
    
    # 构建记忆上下文
    memory_context = "相关的用户信息：\n"
    for memory in relevant_memories:
        memory_context += f"- [{memory.created_at}] {memory.original_text}\n"
    
    messages = [
        {"role": "system", "content": f"""你是一个友好的AI助手，请参考以下用户相关信息：
        {memory_context}
        在回答时，适当地运用这些信息来个性化对话。"""},
        {"role": "user", "content": user_input}
    ]
    
    try:
        response = chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"对话过程出现错误: {str(e)}"

# 初始化记忆管理器
if 'memory_manager' not in st.session_state:
    st.session_state.memory_manager = MemoryManager()

# 页面标题
st.title("智能对话反思系统")

# 侧边栏：记忆搜索
with st.sidebar:
    st.subheader("记忆搜索")
    search_query = st.text_input("搜索记忆：")
    if search_query:
        memories = get_relevant_memories(search_query)
        st.write("相关记忆：")
        for memory in memories:
            st.write(f"[{memory.created_at}] {memory.original_text}")

# 主界面：对话
user_input = st.text_input("请输入您的消息：")

if user_input:
    # 记录对话历史
    st.session_state.conversation_history.append({
        "role": "user",
        "time": str(datetime.now()),
        "content": user_input
    })
    
    # 生成回复
    response = chat_with_memory(user_input)
    st.session_state.conversation_history.append({
        "role": "assistant",
        "time": str(datetime.now()),
        "content": response
    })
    
    # 显示回复
    st.write("AI:", response)
    
    # 每隔10轮对话进行一次反思
    if len(st.session_state.conversation_history) % 10 == 0:
        with st.spinner('正在进行对话反思...'):
            reflection = reflect_on_conversation(st.session_state.conversation_history[-10:])
            st.success("完成对话反思！")

# 显示对话历史
st.subheader("对话历史")
for message in st.session_state.conversation_history:
    prefix = "用户:" if message["role"] == "user" else "AI:"
    st.text(f"{prefix} [{message['time']}] {message['content']}")

# 显示所有记忆
st.subheader("系统记忆")
memory_manager = st.session_state.get('memory_manager')
if memory_manager:
    for memory in memory_manager.memory_data:
        st.text(f"[{memory.created_at}] {memory.labels}: {memory.original_text}")
