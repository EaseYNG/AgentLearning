import json
import uuid
import os
from typing import List, Dict, Any

class HistoryManager:
    def __init__(self):
        self.single_history : List[Dict] = []
        self.long_history : List[Dict] = []
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.memory_dir = os.path.join(self.base_dir, "memory")
        self.long_history_path = os.path.join(self.memory_dir, "long_history.json")
        self.single_history_path = os.path.join(self.memory_dir, "single_history.json")
        
        # 确保目录存在
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
        self.load()

    def load(self):
        self.clear() # 清空单次历史
        try:
            if os.path.exists(self.long_history_path):
                with open(self.long_history_path, 'r', encoding='utf-8') as f:
                    self.long_history = json.load(f)
            else:
                self.long_history = []
        except Exception as e:
            print(f"加载长期历史错误：{e}")

    def add(self, message: Dict[str, Any]):
        '''添加字典到单次历史'''
        self.single_history.append(message)
        try:
            with open(self.single_history_path, 'w', encoding='utf-8') as f:
                json.dump(self.single_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存单次历史错误：{e}")

    def get(self) -> List[Dict[str, Any]]:
        '''获取单次历史'''
        return self.single_history

    def clear(self):
        try:
            self.single_history = []
            with open(self.single_history_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
        except Exception as e:
            print(f"清空单次历史错误：{e}")

    def adds(self, messages: List[Dict]):
        '''添加单次历史到长期历史'''
        uid = uuid.uuid4()
        temp = {
            "chat_id": str(uid),
            "chat_history": messages
        }
        try:
            self.long_history.append(temp)
            with open(self.long_history_path, 'w', encoding='utf-8') as f:
                json.dump(self.long_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新长期历史错误：{e}")

    def update(self):
        '''将单次对话历史加入长期历史'''
        self.adds(self.single_history)

    def list(self) -> List[Dict]:
        '''获取全部历史列表'''
