"""
    session_manager.py
"""

import abc
import os
import json
import glob
import threading
import time
import uuid
from datetime import datetime, timedelta

class Session:
    """ Session类，表示一个会话 """
    def __init__(self, session_id, conversation, session_path, session_name, **kwargs):
        self.session_id = session_id
        self.conversation = conversation
        self.session_path = session_path
        self.session_name = session_name
        # 其他会话相关属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """ 将Session对象转换为字典 """
        session_dict = {
            "session_id": self.session_id,
            "conversation": self.conversation,
            "session_path": self.session_path,
            "session_name": self.session_name
        }
        # 添加其他属性
        for attr, value in self.__dict__.items():
            if attr not in session_dict:
                session_dict[attr] = value
        return session_dict
    
    @classmethod
    def from_dict(cls, session_dict):
        """ 从字典创建Session对象 """
        return cls(**session_dict)

class LocalSessionManager:
    """ LocalSessionManager，管理本地会话 """
    def __init__(self, path="./data/sessions"):
        self.root = path
        self.locks = {}
    
    def new(self, control_params):
        """ 创建新的会话 """
        session_data = {**control_params}
        session_data["session_id"] = generate_session_id()
        session_data["conversation"] = []
        session_data["session_path"] = self.root
        session_data.setdefault("session_name", "Default Session")  # 设置默认值
        os.makedirs(session_data["session_path"], exist_ok=True)
        
        # 创建Session对象
        session = Session.from_dict(session_data)
        self.save(session)
        return session
    
    def save(self, session):
        """ 保存会话 """
        session_path = os.path.join(session.session_path, f"{session.session_id}.json")
        
        # 获取或创建锁
        if session_path not in self.locks:
            self.locks[session_path] = threading.Lock()
        lock = self.locks[session_path]
        
        lock.acquire()
        try:
            with open(session_path, "w", encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=4, ensure_ascii=False)
        finally:
            lock.release()
    
    def get(self, control_params):
        """ 获取会话 """
        session_id = control_params.get("session_id")
        session_name = control_params.get("session_name")
        
        if session_id:
            # 通过session_id获取会话
            session_json = os.path.join(self.root, f"{session_id}.json")
            if not os.path.exists(session_json):
                return None
            try:
                with open(session_json, encoding='utf-8') as file:
                    session_data = json.load(file)
                    # 检查是否被删除
                    if session_data.get("deleted"):
                        return None
                    # 创建Session对象
                    return Session.from_dict(session_data)
            except Exception as e:
                print(f"JSON error in {session_json} with error: {str(e)}")
                return None
        elif session_name:
            # 通过session_name获取会话，可能有多个匹配
            user_sessions_path = os.path.join(self.root, "*.json")
            files = glob.glob(user_sessions_path)
            matching_sessions = []
            for session_file in files:
                try:
                    with open(session_file, encoding='utf-8') as f:
                        session_data = json.load(f)
                        if session_name.startswith(session_data.get("session_name", "")) and not session_data.get("deleted"):
                            matching_sessions.append(Session.from_dict(session_data))
                except Exception as e:
                    print(f"JSON error in {session_file} with error: {str(e)}")
            return matching_sessions[0]
        else:
            return None
    
    def list(self):
        """ 列出所有会话 """
        user_sessions_path = os.path.join(self.root, "*.json")
        files = glob.glob(user_sessions_path)
        files.sort(key=os.path.getctime, reverse=True)
        
        today, start_of_week, start_of_month, start_of_year = get_start_of_day_week_month_year()
        
        sessions = []
        for session_file in files:
            session_id = os.path.basename(session_file).split(".")[0]
            session = self.get({"session_id": session_id})
            if session is None:
                continue
            
            session_name = session.session_name
            create_time = datetime.fromtimestamp(os.path.getctime(session_file))
            consultation_period = calc_consultation_period(
                create_time, today, start_of_week, start_of_month, start_of_year)
            
            sessions.append({
                "session_id": session_id,
                "session_name": session_name + ": " + session_id[:4],
                "consultation_period": consultation_period,
                "create_time": create_time.strftime('%Y-%m-%d %H:%M')
            })
        
        return sessions


def generate_session_id():
    """
    生成一个随机的session_id。
    
    Args:
        无。
    
    Returns:
        一个由32个字符组成的字符串，形式如 '8a8c9692-906f-499a-b25c-906124e50e12'。
    
    """
    session_id = str(uuid.uuid4())
    return session_id

def get_start_of_day_week_month_year():
    """ get_start_of_day_week_month_year"""
    now = datetime.now()
    today = now.date()
    start_of_week = (now - timedelta(days=now.weekday())).date()
    start_of_month = now.replace(day=1).date()
    start_of_year = now.replace(month=1, day=1).date()

    return today, start_of_week, start_of_month, start_of_year


def calc_consultation_period(create_time, today, start_of_week, start_of_month, start_of_year):
    """ calc_consultation_period """
    create_date = create_time.date()
    if create_date == today:
        consultation_period = "Today"
    elif create_date >= start_of_week:
        consultation_period = "ThisWeek"
    elif create_date >= start_of_month:
        consultation_period = "ThisMonth"
    elif create_date >= start_of_year:
        consultation_period = "ThisYear"
    else:
        consultation_period = "Earlier"

    return consultation_period

if __name__ == "__main__":
    # 创建会话管理器
    manager = LocalSessionManager(path="./data/sessions")

    # 创建新的会话，指定session_name
    control_params = {"session_name": "会话1"}
    new_session = manager.new(control_params)
    print(new_session.session_id)  # 输出新生成的会话ID
    print(new_session.session_name)  # 输出会话名称

    # 通过session_id获取会话
    session_by_id = manager.get({"session_id": new_session.session_id})
    print(session_by_id.session_name)  # 输出会话名称

    # 通过session_name获取会话
    sessions_by_name = manager.get({"session_name": "会话1"})
    for session in sessions_by_name:
        print(session.session_id, session.session_name)

    # 列出所有会话
    all_sessions = manager.list()
    for s in all_sessions:
        print(s["session_id"], s["session_name"], s["create_time"])