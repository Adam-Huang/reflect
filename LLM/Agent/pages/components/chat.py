import os
import json
import logging
from datetime import datetime
from typing import List

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

def build_system_prompt_with_memory(query: str, environment: dict) -> (str, str):
    """构建系统提示"""
    workflow_name = ""
    
    # 获取相关长期记忆
    relevant_memories = get_relevant_memories(query)
    # 构建记忆上下文
    memory_context = "\n相关的用户信息：\n"
    for memory in relevant_memories:
        memory_context += f"\ncreated at [{memory.created_at}]\nsummary:\n{memory.summary}\n"
        if "workflow" in memory.labels:
            workflow_name = memory.trigger
    
    # 构建短期记忆
    workflow_overview = "\n".join([
        f"{step['stage']}:{step['action_name']} -> {step['parameters']}" for step in environment.get("workflow", [])
        ])
    environment_info = fetch_info_from_environment(environment, query)

    if workflow_overview:
        memory_context += f"\n\n当前正在执行的工作流：\n{workflow_overview}\n"

    if environment_info:
        memory_context += f"\n\n当前涉及的环境信息：\n{environment_info}\n"
    
    prompt = "你是一个友好的AI助手，请参考以下用户相关信息：\n" + memory_context + "\n在回答时，适当地运用这些信息来针对性地回答。"
    return prompt, workflow_name

def chat_with_memory_and_history(user_input: str, system_prompt: str = None) -> str:
    """与用户对话，包含记忆上下文"""
    # 添加用户消息
    with st.chat_message("user"):
        with st.expander("System Prompt"):
            st.write(system_prompt)
        st.write(user_input)
    
    messages =  [{"role": "system", "content": system_prompt}] + \
        [{"role": m["role"], "content": m["content"]} for m in st.session_state.quoted_history] + \
        [{"role": "user", "content": user_input}]
    
    # 记录对话历史
    st.session_state.session.conversation.append({
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
    st.session_state.session.conversation.append({
        "role": "assistant",
        "time": str(datetime.now()),
        "content": response,
        "id": str(datetime.now().timestamp())
    })
    
    st.session_state.session_manager.save(st.session_state.session)
    
    # 清空被引用的对话历史
    clear_quotes()
    return response

def llm_call(content: str, environment: dict) -> str:
    """LLM 调用
    """
    system_prompt, workflow_name = build_system_prompt_with_memory(content, environment)
    response = chat_with_memory_and_history(content, system_prompt)
    return response, workflow_name

register_function("llm_call", llm_call)
register_function("user_check", interactive)
abilities = function_registry

def convert_step_to_function(step: dict, environment: dict) -> dict:
    """
    Convert a step in workflow to a function call.
    
    Args:
        step (dict): Step in workflow
        environment (dict): Environment variables
        
    Returns:
        dict: Function call
    """
    function = step.get("action_name", "")
    params = step.get("parameters", {}).copy()  # Create a copy to avoid modifying original
    
    # Process step dependencies
    for key, value in params.items():
        if isinstance(value, str) and value.startswith("STEP"):
            if value in environment:
                params[key] = environment[value]
    
    # For logging, create a safe copy of params without circular references
    log_params = params.copy()
    if function == "llm_call" and "environment" in log_params:
        log_params["environment"] = "<environment dict>"
    
    logging.info(f"Executing {function} with params: {json.dumps(log_params, ensure_ascii=False)}")
    
    # Add environment to params for llm_call
    if function == "llm_call":
        params["environment"] = environment
        
    result = abilities.get(function)(**params)
    try:
        ret, more = result
    except (ValueError, TypeError):
        ret = result
        more = ""
    
    if function != "llm_call":
        st.markdown(f"Function {function} | more {more} | returned:\n ```json\n{ret}```")
    return {"result": ret, "more": more}

def do_workflow(workflow: str):
    """执行工作流"""
    workflow = json_exact(workflow)
    
    for i, step in enumerate(workflow):
        step.update({"step": f"STEP{i+1}"})
    
    environment = {"workflow": workflow}
    for step in workflow:
        response = convert_step_to_function(step, environment)
        # TODO: below, abstractly, is define the next action type to totally task, which is one of the following:
        # 1. I've finished my task, and you can do the next task.
        # 2. I need do more operations, to finish my task.
        # 3. I need more information, to finish my task.
        # above, is action method or type, which is not data.
        # So, when we regard llm_call as a function, which real function like get_weather etc, need control the next action type, too.

        # OK, now, considering how many action types or methods? 
        # first, regard April as a employee, when boss gave him a task, he has serveral results:
        # - Finished or Confusion, which means he will give a feedback to the boss.
        # - Find something, resource, communication, etc, which is trying to finish the task.
        # Workflow processing, need to consider these action types.
        if isinstance(response, dict) and response.get("more"):
            workflow = response["more"]
            logging.warning(f"This is {step['action_name']} workflow. Please follow the instructions.")
            response = do_workflow(response["result"])
            logging.info(f"Workflow {step['action_name']} completed.")
        
        if isinstance(response, dict):
            environment.update({step["step"]: response["result"]})
        else:
            environment.update({step["step"]: response})

    return response