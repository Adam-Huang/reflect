import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4

import streamlit as st
from openai import OpenAI

from core.memory import Memory, MemoryManager
from functions.re_exact import json_exact
from functions import function_registry, register_function
from .history import clear_quotes
from .interactive import interactive

# 初始化 OpenAI Chat 客户端
chat_client = OpenAI(
    base_url=os.getenv("CHAT_BASE_URL"),
    api_key=os.getenv("CHAT_API_KEY")
)

april_prompt = """
你是一个诚实、稳健的AI助手，尽力完成用户的要求。

你有很多能力，或者说工具，当你输出
```json
{
    "function_name": "xxx",
    "parameters": {}
}
```
时，可以调用相关的能力

注意：
1. 请参考相关记忆
2. 尽力去完成（不要仅告诉我该怎么做！）。
  - 如果不清楚用户的要求（缺少信息），请明确提出。
  - 如果你无法实现（缺少必要物料，如XX信息、YY工具或者ZZ能力），请明确提出。

已知能力有：


"""

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
    # Maybe: triggers 需要进行排序，字符越长越靠前，保证后面有最长字符优先匹配的特性
    # Idea: label 可以用在匹配后填充上，填充到 prompt 的不同位置，或者 function_call 里
    for trigger in memory_manager.triggers:
        # 输入里有 trigger 词，直接匹配
        if trigger in query:
            relevant_memories.extend(memory_manager.search_memory(query=trigger, search_type="trigger"))
    
    return relevant_memories

def fetch_info_from_environment(environment: dict, prompt: str) -> str:
    """从环境变量中提取信息"""
    environment_info = ""
    for key, value in environment.items():
        if key in prompt:
            environment_info += f"{key} result: {value}\n"
    return environment_info

def build_system_prompt_with_memory(query: str, plan: str) -> str:
    """构建系统提示"""
    # fetch long-term memories by query
    relevant_memories = get_relevant_memories(query)
    
    # build relevant memories context
    memory_context = "\n# 和用户有关的记忆：\n"
    for memory in relevant_memories:
        memory_context += f"\ncreated at [{memory.created_at}]\nsummary:\n{memory.original_text}\n"
    
    if plan:
        memory_context += f"\n\n当前正在执行的计划：\n{plan}\n"
    

    prompt = april_prompt + memory_context
    return prompt

def chat_with_conversation(user_input: str, system_prompt: str = "", history: List[Dict] = None) -> str:
    """与用户对话，包含记忆上下文"""
    # 添加用户消息
    with st.chat_message("user"):
        with st.expander("System Prompt"):
            st.write(system_prompt)
        st.write(user_input)
    
    messages =  [{"role": "system", "content": system_prompt}] + \
        [{"role": m["role"], "content": m["content"]} for m in history] + \
        [{"role": "user", "content": user_input}]
    
    previous_ids = []
    for m in history:
        if m["role"] == "assistant":
            previous_ids.append(m.get("id"))
    
    # 记录对话历史
    st.session_state.session.conversation.append({
        "role": "user",
        "time": str(datetime.now()),
        "content": user_input,
        "id": "u_" + str(uuid4()),
        "previous_ids": previous_ids,
    })

    # 生成并显示AI回复
    with st.chat_message("assistant"):
        stream = chat_client.chat.completions.create(
            model=os.getenv("CHAT_MODEL"),
            messages=messages,
            stream=True,
        )
        try:
            reasoning_response = ""
            if hasattr(stream, "reasoning_content"):
                reasoning_response += stream.reasoning_content
                print(stream.reasoning_content, end="")
            response = st.write_stream(stream)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error(f"Chat error: {str(e)}", exc_info=True)
    
    # 添加AI回复到消息记录
    st.session_state.session.conversation.append({
        "role": "assistant",
        "time": str(datetime.now()),
        "content": response,
        "id": "a_" + str(uuid4()),
        "model": {
            "name": os.getenv("CHAT_MODEL"),
        }
    })
    
    st.session_state.session_manager.save(st.session_state.session)
    
    # 清空被引用的对话历史
    clear_quotes()
    return response

def think(content: str, environment: dict) -> str:
    """LLM 调用
    """
    system_prompt = build_system_prompt_with_memory(content, environment.get("plan", ""))
    response = chat_with_conversation(content, system_prompt, environment.get("conversation", []))
    return response

def execute_action(action: str, environment: dict) -> str:
    """
    Execute action
    
    Args:
        action (str): Action in workflow
        environment (dict): Environment variables
        
    Returns:
        dict: Function call
    """
    try:
        action = json_exact(action)
    except Exception as e:
        logging.error(f"Error parsing action: {e}")
        return f"Error parsing action: {e}"

    function = action.get("action_name", "")
    params = action.get("parameters", {}).copy()  # Create a copy to avoid modifying original
    
    # Add environment to params for think
    if function == "think":
        return think(params["content"], environment)

    try:
        result = abilities.get(function)(**params)
    except Exception as e:
        logging.error(f"Error executing {function}: {e}")
        result = f"Error executing {function}: {e}"
    
    return result

def run_plan(plan: str) -> str:
    """执行计划
    
    Args:
        plan (str): 计划
    Returns:
        str: 执行的结果
    """
    environment = {
        "plan": plan,
        "conversation": []
    }
    
    # thinking
    init_action = "`@plan_decide_next`\n`@function_description`\n开始执行第一步"
    next_action = think(init_action, environment)
    environment["conversation"].extend([
        {"role": "user", "time": str(datetime.now()), "content": init_action, "id": str(datetime.now().timestamp())}, 
        {"role": "assistant", "time": str(datetime.now()), "content": next_action, "id": str(datetime.now().timestamp())}
    ])

    while isinstance(next_action, dict) or (isinstance(next_action, str) and "finished" not in next_action.lower()):
        # action
        response = execute_action(next_action, environment)
        # Show as user called the function
        with st.chat_message("user"):
            st.markdown(response)
        
        # thinking
        next_action = think(
            "`@plan_decide_next`\n`@function_description`\n" + f"action_name: {next_action['action_name']}\nparameters: {next_action['parameters']}\nresult: {response}", 
            environment)
        # Show as assistant called the function
        with st.chat_message("assistant"):
            st.markdown(next_action)
        
        environment["conversation"].append({
            "role": "user",
            "time": str(datetime.now()),
            "content": response,
            "id": str(datetime.now().timestamp())
        })
        
        environment["conversation"].append({
            "role": "assistant",
            "time": str(datetime.now()),
            "content": next_action,
            "id": str(datetime.now().timestamp())
        })

    return response

register_function("think", think)
register_function("run_plan", run_plan)
abilities = function_registry