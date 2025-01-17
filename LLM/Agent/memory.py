
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import numpy as np
import faiss
import openai
import os

@dataclass
class Memory:
    id: str
    original_text: str
    summary: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    labels: List[str] = field(default_factory=list)
    trigger: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    metadata: Optional[dict] = None

    def update(self, new_text: str = None, new_summary: str = None):
        """Update memory content and timestamps"""
        if new_text:
            self.original_text = new_text
        if new_summary:
            self.summary = new_summary
        self.updated_at = datetime.now()

class MemoryManager:
    def __init__(self):
        self.dimension = 1536  # OpenAI ada-002 embedding dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.memory_data = []
        self.labels = set()
        self.triggers = set()
        self.load_memory()

    def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的向量嵌入"""
        client = openai.OpenAI(
            base_url=os.getenv("EMBEDDING_BASE_URL"),
            api_key=os.getenv("EMBEDDING_API_KEY")
        )
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def add_memory(self, memory_text: str, summary: str, labels: List[str] = None, trigger: str = None):
        """添加新的记忆"""
        embedding = None # self.get_embedding(summary)
        # self.index.add(embedding.reshape(1, -1))
        
        memory = Memory(
            id=str(len(self.memory_data)),
            original_text=memory_text,
            summary=summary,
            labels=labels or [],
            trigger=trigger,
            embedding=embedding
        )
        self.memory_data.append(memory)
        self.labels.update(memory.labels)
        if memory.trigger:
            self.triggers.add(memory.trigger)
        self.save_memory()

    def search_memory(self, query: str, labels: List[str] = None, k: int = 5, search_type: str = "vector", exact_match: bool = False) -> List[Memory]:
        """Search memories using different methods
        
        Args:
            query: The search query
            k: Number of results to return
            search_type: One of "vector", "keyword", "label", or "trigger"
            exact_match: For keyword search, whether to match exactly
            
        Returns:
            List of matching Memory objects
        """
        if search_type == "vector":
            query_embedding = None # self.get_embedding(query)
            distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.memory_data):
                    results.append(self.memory_data[idx])
            return results
            
        elif search_type == "keyword":
            if exact_match:
                matches = [mem for mem in self.memory_data 
                       if query in mem.original_text or query in mem.summary]
            else:
                query = query.lower()
                matches = [mem for mem in self.memory_data 
                       if query in mem.original_text.lower() or 
                          query in mem.summary.lower()]
            return matches[:k]
                          
        elif search_type == "trigger":
            matches = [mem for mem in self.memory_data if mem.trigger == query]
            return matches
        
        elif search_type == "label":
            if labels is None or not labels:
                raise ValueError("labels must be provided when search_type='label'")
            if isinstance(labels, str):
                labels = [labels]
            matches = [mem for mem in self.memory_data if any(label in mem.labels for label in labels)]
            return matches[:k]

        else:
            raise ValueError(f"Invalid search type: {search_type}")

    def update_memory(self, memory_id: str, new_text: str = None, new_summary: str = None, 
                     new_labels: List[str] = None, new_trigger: str = None):
        """Update an existing memory
        
        Args:
            memory_id: ID of memory to update
            new_text: New text content
            new_summary: New summary
            new_labels: New labels
            new_trigger: New trigger
        """
        for mem in self.memory_data:
            if mem.id == memory_id:
                mem.update(new_text, new_summary)
                if new_labels is not None:
                    mem.labels = new_labels
                if new_trigger is not None:
                    mem.trigger = new_trigger
                    
                # Update embedding if text changed
                # if new_summary:
                #     new_embedding = self.get_embedding(new_summary)
                #     self.index.add(new_embedding.reshape(1, -1))
                self.save_memory()
                return
                
        raise ValueError(f"Memory with id {memory_id} not found")

    def delete_memory(self, memory_id: str):
        """Delete a memory by ID
        
        Args:
            memory_id: ID of memory to delete
        """
        for i, mem in enumerate(self.memory_data):
            if mem.id == memory_id:
                # Remove from FAISS index
                self.index.remove_ids(np.array([i], dtype=np.int64))
                # Remove from memory data
                del self.memory_data[i]
                self.save_memory()
                return
                
        raise ValueError(f"Memory with id {memory_id} not found")

    def save_memory(self):
        """保存记忆到文件"""
        memory_state = {
            'memory_data': [{
                'id': mem.id,
                'created_at': mem.created_at.isoformat(),
                'updated_at': mem.updated_at.isoformat(),
                'original_text': mem.original_text,
                'summary': mem.summary,
                'labels': mem.labels,
                'trigger': mem.trigger,
                'embedding': mem.embedding.tolist() if mem.embedding is not None else None
            } for mem in self.memory_data]
        }
        with open('./data/labels.json', 'w') as f:
            json.dump(list(self.labels), f)
        with open('./data/triggers.json', 'w') as f:
            json.dump(list(self.triggers), f)
        with open('./data/memory_state.json', 'w') as f:
            json.dump(memory_state, f, indent=4, ensure_ascii=False)
        faiss.write_index(self.index, 'index.faiss')

    def load_memory(self):
        """从文件加载记忆"""
        try:
            with open('./data/memory_state.json', 'r') as f:
                data = json.load(f)
                self.memory_data = [
                    Memory(
                        id=mem['id'],
                        created_at=datetime.fromisoformat(mem['created_at']),
                        updated_at=datetime.fromisoformat(mem['updated_at']),
                        original_text=mem['original_text'],
                        summary=mem['summary'],
                        labels=mem['labels'],
                        trigger=mem['trigger'],
                        embedding=np.array(mem['embedding'], dtype=np.float32) if mem['embedding'] is not None else None
                    ) for mem in data['memory_data']
                ]
            self.index = faiss.read_index('./data/index.faiss')
        except FileNotFoundError:
            self.index = faiss.IndexFlatL2(self.dimension)
        
        try:
            with open('./data/labels.json', 'r') as f:
                self.labels = set(json.load(f))
            with open('./data/triggers.json', 'r') as f:
                self.triggers = set(json.load(f))
        except FileNotFoundError:
            for mem in self.memory_data:
                self.labels.update(mem.labels)
                if mem.trigger:
                    self.triggers.add(mem.trigger)

# Streamlit UI
import streamlit as st
@st.dialog("Add your Memory")
def add_memory_dialog():
    memory_text = st.text_area("Memory Text")
    memory_summary = st.text_area("Summary")
    memory_labels = st.text_input("Labels, Using , to separate. For example: label1, label2")
    memory_trigger = st.text_input("Trigger")
    submit_button = st.button(label='Submit Memory')
    if submit_button:
        st.session_state.memory_manager.add_memory(
            memory_text=memory_text,
            summary=memory_summary,
            labels=memory_labels.split(','),
            trigger=memory_trigger if memory_trigger else None
        )
        st.success("Memory added successfully!")
        st.rerun()

@st.dialog("Show your Memory")
def show_memory_dialog():
    memory_manager = st.session_state.memory_manager
    
    search_type = st.selectbox("选择查询类型", ["vector", "keyword", "label", "trigger"])
    
    if search_type == "vector":
        query = st.text_input("输入查询文本")
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5)
        if st.button("查询"):
            memories = memory_manager.search_memory(query, k=k, search_type=search_type)
            display_memories(memories, memory_manager)
    elif search_type == "keyword":
        query = st.text_input("输入关键词")
        exact_match = st.checkbox("精确匹配")
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5)
        if st.button("查询"):
            memories = memory_manager.search_memory(query, k=k, search_type=search_type, exact_match=exact_match)
            display_memories(memories, memory_manager)
    elif search_type == "label":
        labels = st.multiselect("选择标签", list(memory_manager.labels), default=[])
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5)
        if st.button("查询"):
            memories = memory_manager.search_memory("", labels=labels, k=k, search_type=search_type)
            display_memories(memories, memory_manager)
    elif search_type == "trigger":
        query = st.selectbox("选择触发词", list(memory_manager.triggers))
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5)
        if st.button("查询"):
            memories = memory_manager.search_memory(query, k=k, search_type=search_type)
            display_memories(memories, memory_manager)
    else:
        st.write("无效的查询类型")

def display_memories(memories, memory_manager):
    if not memories:
        st.write("没有找到匹配的记忆")
        return
    for mem in memories:
        st.write(f"ID: {mem.id} | 创建时间: {mem.created_at} | 更新时间: {mem.updated_at}")
        st.write(f"摘要: {mem.summary}")
        with st.expander("显示原文"):
            st.markdown(mem.original_text)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"删除记忆 {mem.id}"):
                memory_manager.delete_memory(mem.id)
                st.write(f"记忆 {mem.id} 已删除")
        with col2:
            if st.button(f"更新记忆 {mem.id}"):
                update_memory_dialog(mem.id, memory_manager)

def update_memory_dialog(memory_id, memory_manager):
    mem = None
    for m in memory_manager.memory_data:
        if m.id == memory_id:
            mem = m
            break
    if mem is None:
        st.write(f"记忆 {memory_id} 不存在")
        return
    
    st.write(f"当前记忆 ID: {mem.id}")
    st.write(f"当前原文: {mem.original_text}")
    st.write(f"当前摘要: {mem.summary}")
    st.write(f"当前标签: {', '.join(mem.labels)}")
    st.write(f"当前触发词: {mem.trigger}")
    
    new_text = st.text_area("新的原文", value=mem.original_text)
    new_summary = st.text_area("新的摘要", value=mem.summary)
    new_labels = st.text_input("新的标签，多个标签用逗号分隔", value=", ".join(mem.labels))
    new_trigger = st.text_input("新的触发词", value=mem.trigger)
    
    if st.button("更新记忆"):
        new_labels_list = [label.strip() for label in new_labels.split(",") if label.strip()]
        memory_manager.update_memory(mem.id, new_text, new_summary, new_labels_list, new_trigger)
        st.write(f"记忆 {mem.id} 已更新")
