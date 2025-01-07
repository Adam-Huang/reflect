
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
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    original_text: str
    summary: str
    labels: List[str] = field(default_factory=list)
    trigger: Optional[str] = None

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
        embedding = self.get_embedding(memory_text)
        self.index.add(embedding.reshape(1, -1))
        
        memory = Memory(
            id=str(len(self.memory_data)),
            original_text=memory_text,
            summary=summary,
            labels=labels or [],
            trigger=trigger
        )
        self.memory_data.append(memory)
        self.save_memory()

    def search_memory(self, query: str, k: int = 5) -> List[Memory]:
        """搜索相关记忆"""
        query_embedding = self.get_embedding(query)
        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.memory_data):
                results.append(self.memory_data[idx])
        return results

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
                'trigger': mem.trigger
            } for mem in self.memory_data],
            'index_data': faiss.serialize_index(self.index).tobytes()
        }
        with open('memory_state.json', 'w') as f:
            json.dump({
                'memory_data': memory_state['memory_data'],
                'index_data': memory_state['index_data'].hex()
            }, f)

    def load_memory(self):
        """从文件加载记忆"""
        try:
            with open('memory_state.json', 'r') as f:
                data = json.load(f)
                self.memory_data = [
                    Memory(
                        id=mem['id'],
                        created_at=datetime.fromisoformat(mem['created_at']),
                        updated_at=datetime.fromisoformat(mem['updated_at']),
                        original_text=mem['original_text'],
                        summary=mem['summary'],
                        labels=mem['labels'],
                        trigger=mem['trigger']
                    ) for mem in data['memory_data']
                ]
                index_bytes = bytes.fromhex(data['index_data'])
                self.index = faiss.deserialize_index(index_bytes)
        except FileNotFoundError:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.memory_data = []
