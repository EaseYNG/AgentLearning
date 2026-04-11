import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import chromadb

def to_md(message, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(message)

def from_md(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read()
    
def append_md(message, file_name):
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(message)

class History:
    def __init__(self):
        os.makedirs("files", exist_ok=True)
        self.load()

    def load(self):
        import json
        try:
            with open("files/chat_history.json", "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = []
    
    def add(self, message):
        self.history.append(message)
        # 保存为JSON格式
        import json
        with open("files/chat_history.json", "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def get(self):
        return self.history

load_dotenv()
client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

def call(message, model="deepseek-chat"):
    chat_history = History()
    user_message = {"role": "user", "content": message}
    chat_history.add(user_message)
    
    messages = chat_history.get()
    
    print("start chat")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    
    assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
    chat_history.add(assistant_message)
    
    return response.choices[0].message.content

message = call(from_md("files/input.md"))

to_md(message, "files/output_buffer.md")
print(message)