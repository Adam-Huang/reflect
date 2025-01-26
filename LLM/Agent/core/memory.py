from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import numpy as np
import faiss
import openai
import os
import sqlite3

@dataclass
class Memory:
    id: int
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
        self.handler = MemoryHandler()
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
        embedding = None  # self.get_embedding(summary)
        # self.index.add(embedding.reshape(1, -1))
 
        memory = Memory(
            id=-1,
            original_text=memory_text,
            summary=summary,
            labels=labels or [],
            trigger=trigger,
            embedding=embedding
        )
        self.save_memory(memory)
 
    def add_label(self, label: str, description: str):
        """添加新label"""
        self.handler.insert_label(label, description)
        self.labels.add(label)
 
    def add_trigger(self, trigger: str, description: str):
        """添加新label"""
        self.handler.insert_trigger(trigger, description)
        self.triggers.add(trigger)
 
    def search_memory(self, query: str, labels: List[str] = None, k: int = 5, search_type: str = "vector",
                      exact_match: bool = False) -> List[Memory]:
        """Search memories using different methods
        
        Args:
            labels:
            query: The search query
            k: Number of results to return
            search_type: One of "vector", "keyword", "label", or "trigger"
            exact_match: For keyword search, whether to match exactly
            
        Returns:
            List of matching Memory objects
        """
        if search_type == "vector":
            query_embedding = None  # self.get_embedding(query)
            distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
 
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.memory_data):
                    results.append(self.memory_data[idx])
            return results[::-1]  # Reverse the results
            
        elif search_type == "keyword":
            if exact_match:
                matches = [mem for mem in self.memory_data 
                           if query in mem.original_text or query in mem.summary]
            else:
                query = query.lower()
                matches = [mem for mem in self.memory_data 
                           if query in mem.original_text.lower() or 
                           query in mem.summary.lower()]
            return matches[::-1][:k]  # Reverse and then take k items
        
        elif search_type == "trigger":
            matches = [mem for mem in self.memory_data if mem.trigger == query]
            return matches[::-1]  # Reverse the results
        
        elif search_type == "label":
            if labels is None or not labels:
                raise ValueError("labels must be provided when search_type='label'")
            if isinstance(labels, str):
                labels = [labels]
            matches = [mem for mem in self.memory_data if any(label in mem.labels for label in labels)]
            return matches[::-1][:k]  # Reverse and then take k items
        
        else:
            raise ValueError(f"Invalid search type: {search_type}")
 
    def update_memory(self, memory_id: int, new_text: str = None, new_summary: str = None,
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
                # self.save_memory(mem)
                self.handler.upd_memory(memory_id, mem)
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
                # self.save_memory(mem)
                self.handler.del_memory(memory_id)
                return
 
        raise ValueError(f"Memory with id {memory_id} not found")
 
    def save_memory(self, memory: Memory):
        """保存记忆到Sqlite"""
        self.handler.insert_memory(memory)
        self.load_memory()
        # faiss.write_index(self.index, './data/memory/index.faiss')
 
    def load_memory(self):
        """从Sqlite加载记忆"""
        self.memory_data = self.handler.query_memories()
        self.labels = self.handler.query_labels()
        self.triggers = self.handler.query_triggers()
        # self.index = faiss.read_index('./data/memory/index.faiss')

    def update_label(self, old_label: str, new_label: str, new_description: str = None):
        """Update a label and its description
        
        Args:
            old_label: The label to update
            new_label: The new label name
            new_description: Optional new description
        """
        # Update in memory
        if old_label in self.labels:
            self.labels.remove(old_label)
            self.labels.add(new_label)
            
        # Update in database
        self.handler.upd_label(old_label, new_label, new_description)
        
        # Update all memories that use this label
        for memory in self.memory_data:
            if old_label in memory.labels:
                memory.labels = [new_label if l == old_label else l for l in memory.labels]
                self.save_memory(memory)
        
        # Reload memory data to ensure consistency
        self.load_memory()

    def delete_label(self, label: str):
        """Delete a label and remove it from all memories
        
        Args:
            label: The label to delete
        """
        # Remove from memory
        if label in self.labels:
            self.labels.remove(label)
            
        # Remove from database
        self.handler.del_label(label)
        
        # Remove from all memories that use this label
        for memory in self.memory_data:
            if label in memory.labels:
                memory.labels.remove(label)
                self.save_memory(memory)

    def update_trigger(self, old_trigger: str, new_trigger: str, new_description: str = None):
        """Update a trigger and its description
        
        Args:
            old_trigger: The trigger to update
            new_trigger: The new trigger name
            new_description: Optional new description
        """
        # Update in memory
        if old_trigger in self.triggers:
            self.triggers.remove(old_trigger)
            self.triggers.add(new_trigger)
            
        # Update in database
        self.handler.upd_trigger(old_trigger, new_trigger, new_description)
        
        # Update all memories that use this trigger
        for memory in self.memory_data:
            if memory.trigger == old_trigger:
                memory.trigger = new_trigger
                self.save_memory(memory)

    def delete_trigger(self, trigger: str):
        """Delete a trigger and remove it from all memories
        
        Args:
            trigger: The trigger to delete
        """
        # Remove from memory
        if trigger in self.triggers:
            self.triggers.remove(trigger)
            
        # Remove from database
        self.handler.del_trigger(trigger)
        
        # Remove from all memories that use this trigger
        for memory in self.memory_data:
            if memory.trigger == trigger:
                memory.trigger = None
                self.save_memory(memory)


class MemoryHandler:
    def __init__(self):
        self.conn = self.connect_db()
        self.create_table()
 
    @staticmethod
    def connect_db(db_name="./data/memory/memory.db"):
        return sqlite3.connect(db_name)
 
    def create_table(self):
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                labels TEXT,
                trigger TEXT,
                embedding BLOB,
                metadata TEXT
            );
            """
        self.conn.execute(create_table_sql)
 
        create_label_sql = """
                CREATE TABLE IF NOT EXISTS Labels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT,
                    description TEXT
                );
                """
        self.conn.execute(create_label_sql)
 
        create_trigger_sql = """
                        CREATE TABLE IF NOT EXISTS Triggers (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            trigger TEXT,
                            description TEXT
                        );
                        """
        self.conn.execute(create_trigger_sql)
        self.conn.commit()
 
    def insert_memory(self, memory):
        insert_sql = """
            INSERT INTO Memory (original_text, summary, created_at, updated_at, labels, trigger, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """
        self.conn.execute(insert_sql, (
            memory.original_text,
            memory.summary,
            memory.created_at,
            memory.updated_at,
            ','.join(memory.labels) if memory.labels else '',  # Join list into comma-separated string
            memory.trigger,
            memory.embedding,  # Assume already in binary format
            json.dumps(memory.metadata) if memory.metadata else None  # Serialize dictionary to JSON string
        ))
        self.conn.commit()
 
    def insert_label(self, label, description):
        insert_sql = """
                INSERT INTO Labels (label, description)
                VALUES (?, ?);
                """
        self.conn.execute(insert_sql, (label, description))
        self.conn.commit()
 
    def insert_trigger(self, trigger, description):
        insert_sql = """
                INSERT INTO Triggers (trigger, description)
                VALUES (?, ?);
                """
        self.conn.execute(insert_sql, (trigger, description))
        self.conn.commit()
 
    def query_memories(self):
        cursor = self.conn.execute("SELECT * FROM Memory;")
        memories = []
        for row in cursor:
            memory = Memory(
                id=row[0],
                original_text=row[1],
                summary=row[2],
                created_at=row[3],
                updated_at=row[4],
                labels=row[5].split(',') if row[5] else [],  # Split comma-separated labels
                trigger=row[6],
                embedding=row[7],  # If embedding is stored as binary, handle appropriately
                metadata=json.loads(row[8]) if row[8] else None  # Assuming metadata is stored as JSON
            )
            memories.append(memory)
            # print(memory)  # 打印每个 Memory 实例
 
        return memories
 
    def query_labels(self):
        cursor = self.conn.execute("SELECT * FROM Labels;")
        labels = set()
        for row in cursor:
            labels.add(row[1])
        return labels
 
    def query_triggers(self):
        cursor = self.conn.execute("SELECT * FROM Triggers;")
        triggers = set()
        for row in cursor:
            triggers.add(row[1])
        return triggers
 
    def upd_memory(self, memory_id, mem):
        update_sql = """
            UPDATE Memory
            SET original_text = ?, summary = ?, labels = ?, trigger = ?, updated_at = ?
            WHERE id = ?;
            """
        self.conn.execute(update_sql,
                          (mem.original_text, mem.summary, ','.join(mem.labels), mem.trigger, datetime.now(),
                           memory_id))
        self.conn.commit()
 
    def del_memory(self, memory_id):
        delete_sql = "DELETE FROM Memory WHERE id = ?;"
        self.conn.execute(delete_sql, (memory_id,))
        self.conn.commit()

    def upd_label(self, old_label: str, new_label: str, new_description: str = None):
        """Update a label in the database"""
        if new_description is not None:
            update_sql = """
                UPDATE Labels
                SET label = ?, description = ?
                WHERE label = ?;
                """
            self.conn.execute(update_sql, (new_label, new_description, old_label))
        else:
            update_sql = """
                UPDATE Labels
                SET label = ?
                WHERE label = ?;
                """
            self.conn.execute(update_sql, (new_label, old_label))
        self.conn.commit()

    def del_label(self, label: str):
        """Delete a label from the database"""
        delete_sql = "DELETE FROM Labels WHERE label = ?;"
        self.conn.execute(delete_sql, (label,))
        self.conn.commit()

    def upd_trigger(self, old_trigger: str, new_trigger: str, new_description: str = None):
        """Update a trigger in the database"""
        if new_description is not None:
            update_sql = """
                UPDATE Triggers
                SET trigger = ?, description = ?
                WHERE trigger = ?;
                """
            self.conn.execute(update_sql, (new_trigger, new_description, old_trigger))
        else:
            update_sql = """
                UPDATE Triggers
                SET trigger = ?
                WHERE trigger = ?;
                """
            self.conn.execute(update_sql, (new_trigger, old_trigger))
        self.conn.commit()

    def del_trigger(self, trigger: str):
        """Delete a trigger from the database"""
        delete_sql = "DELETE FROM Triggers WHERE trigger = ?;"
        self.conn.execute(delete_sql, (trigger,))
        self.conn.commit()
