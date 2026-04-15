import json
import uuid
from typing import List, Dict, Any

class HistoryManager:
    def __init__(self):
        self.single_history : List[Dict]
        self.long_history : List[Dict]
        self.load()

    def load(self):
        self.clear() # 清空单次历史
        try:
            with open("./memory/long_history.json", 'r', encoding='utf-8') as f:
                self.long_history = json.load(f)
        except FileNotFoundError as e:
            print(f"文件不存在：{e}")
            self.single_history = []
            self.long_history = []
        except PermissionError as p:
            print(f"权限错误：{p}")
        except Exception as e:
            print(f"错误：{e}")

    def add(self, message: Dict[str, Any]):
        '''添加字典到单次历史'''
        self.single_history.append(message)
        try:
            with open("./memory/single_history.json", 'w', encoding='utf-8') as f:
                json.dump(self.single_history, f, ensure_ascii=False, indent=2)
        except FileNotFoundError as e:
            print(f"文件不存在：{e}")
        except PermissionError as p:
            print(f"权限错误：{p}")
        except Exception as e:
            print(f"错误：{e}")

    def get(self) -> List[Dict[str, Any]]:
        '''获取单次历史'''
        return self.single_history

    def clear(self):
        try:
            self.single_history = []
            with open("./memory/single_history.json", 'w', encoding='utf-8') as f:
                json.dump([], f)
        except FileNotFoundError as e:
            print(f"文件不存在：{e}")
        except PermissionError as p:
            print(f"权限错误：{p}")
        except Exception as e:
            print(f"错误：{e}")

    def adds(self, messages: List[Dict]):
        '''添加单次历史'''
        uid = uuid.uuid4()
        temp = {
            "chat_id": str(uid),
            "chat_history": messages
        }
        try:
            self.long_history.append(temp)
            with open("./memory/long_history.json", 'w', encoding='utf-8') as f:
                json.dump(self.long_history, f, ensure_ascii=False, indent=2)
        except FileNotFoundError as e:
            print(f"文件不存在：{e}")
        except PermissionError as p:
            print(f"权限错误：{p}")
        except Exception as e:
            print(f"错误：{e}")

    def update(self):
        '''将单次对话历史加入长期历史'''
        self.adds(self.single_history)

    def list(self) -> List[Dict]:
        '''获取全部历史列表'''
