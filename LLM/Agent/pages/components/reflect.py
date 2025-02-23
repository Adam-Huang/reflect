import os
import re
import json
import traceback
from typing import List, Dict
import logging

import streamlit as st
from openai import OpenAI

from core.memory import Environment
from .chat import think, run_plan

# 初始化 OpenAI Chat 客户端
chat_client = OpenAI(
    base_url=os.getenv("MEM_BASE_URL"),
    api_key=os.getenv("MEM_API_KEY")
)

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
"""

def reflect_on_conversation(conversation_history: List[Dict], prompt: str) -> str:
    """对话反思，分析用户特征和习惯"""
    try:
        logging.info(f"Starting reflection on {len(conversation_history)} conversation items")
        env = Environment()
        env.publish("env://conversation_history", conversation_history)
        
        reflection_stream = chat_client.chat.completions.create(
            model=os.getenv("MEM_MODEL"),
            messages=[
                {"role": "system", "content": "你是一个专注于分析和总结的AI助手。"},
                {"role": "user", "content": prompt.format(conversations="\n".join([f"{c['role']} - {c['content']}" for c in conversation_history]))},
            ],
            stream=True,
        )
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
