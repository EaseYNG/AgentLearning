import os
from datetime import datetime
from openai import OpenAI
import time
import typing

from db_manager import DBManager

def to_md(message, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(message)

def from_md(file_name) -> str:
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read()
    
def append_md(message, file_name):
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(message)

# 对话历史
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
        
        import json
        with open("files/chat_history.json", "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def get(self):
        return self.history
    
    def clear(self):
        self.history = []
        
        import json
        with open("files/chat_history.json", "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

# 定义客户端
client = OpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 调用api（非流式&流式）
def call(message, model="qwen3.5-flash"):
    '''非流式chat'''
    chat_history = History()

    user_message = {"role": "user", "content": f"{message}"}
    chat_history.add(user_message)
    messages = chat_history.get()
    
    print("----- start chat -----")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False
    )

    assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
    chat_history.add(assistant_message)
    print("----- chat finished -----")
    return response.choices[0].message.content

def call_stream(message, model="qwen3.5-flash"):
    '''流式chat生成器：不断生成流式输出块'''
    chat_history = History()
    user_message = {"role": "user", "content": message}
    chat_history.add(user_message)
    messages = chat_history.get()

    chunks = []

    print("----- chat start -----")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )
    for c in response:
        if c.choices[0].delta.content is not None:
            content = c.choices[0].delta.content
            chunks.append(content)
            yield content
    
    full_str = ''.join(chunks)
    chat_history.add({"role": "assistant", "content": f"{full_str}"})
    print()
    print("----- chat finished -----")

# function calling
def fast_pow(a, n) -> int:
    res = 1
    while(n > 0):
        if(n & 1):
            res *= a
        a *= a
        n >>= 1
    return res

tools = [
    {
        "type": "function",
        "function": {
            "name": "fast_pow",
            "description": "使用快速幂算法计算a^n",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "底数a"},
                    "n": {"type": "integer", "description": "指数n"}
                },
            "required": ["a", "n"]
            }
        }
    },
]

def call_tools(message: str, model="qwen3.5-flash"):
    '''非流式chat'''
    chat_history = History()

    user_message = {"role": "user", "content": message}
    chat_history.add(user_message)
    messages = chat_history.get()
    
    print("----- start chat -----")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
    chat_history.add(assistant_message)
    print("----- chat finished -----")
    return response.choices[0].message.content

# 流式输出到控制台
res_str = []
for c in call_stream(from_md("./files/input.md")):
    res_str.append(c)
    print(c, end='', flush=True)
    time.sleep(0.1)

to_md(''.join(res_str), "./files/output_buffer.md")

# res_str = call_tools(from_md("./files/input.md"))

# print(res_str)
# to_md(res_str, "./files/output_buffer.md")