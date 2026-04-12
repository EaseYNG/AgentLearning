import os
from datetime import datetime
from openai import OpenAI
import time
import typing
import json

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
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 调用api（非流式&流式）
def call(message, model="deepseek-chat"):
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

def call_stream(message, model="deepseek-chat"):
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
def get_weather(city: str):
    return f"The weather in {city} is sunny."

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取某城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "要查询的城市名"},
                },
            "required": ["city"]
            }
        }
    },
]

# 字符串-函数映射
FUNC_MAP = {
    "get_weather": get_weather
}

def call_tools(message: str, model="deepseek-chat"):
    '''非流式chat
    使用工具的调用'''
    chat_history = History()

    # 格式化用户输入
    user_message = {"role": "user", "content": message}
    chat_history.add(user_message)
    
    print("----- start chat -----")
    first_response = client.chat.completions.create(
        model=model,
        messages=chat_history.get(),
        tools=tools,
        tool_choice="auto"  # 改为 auto，让模型自己决定是否调用
    )

    msg = first_response.choices[0].message
    
    # 必须把第一轮的 assistant 消息完整加入历史（包含 tool_calls）
    # 使用 model_dump 转换为字典，方便存储到 json
    chat_history.add(msg.model_dump(exclude_none=True))

    # 如果模型没有调用工具，直接返回内容
    if not msg.tool_calls:
        return msg.content or ""
    
    # 成功调用工具的情况，遍历所有工具调用
    for tool_call in msg.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # 调用对应方法
        if func_name in FUNC_MAP:
            print(f"Calling tool: {func_name} with args: {args}")
            result = FUNC_MAP[func_name](**args)
            
            # 将工具执行结果加入历史
            chat_history.add({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
        else:
            print(f"Tool {func_name} not found in FUNC_MAP")

    # 创建第二次请求：模型会根据历史中的 tool_calls 和 tool 结果生成最终回答
    second_request = client.chat.completions.create(
        model=model,
        messages=chat_history.get(),
        tools=tools
    )

    final_msg = second_request.choices[0].message
    chat_history.add(final_msg.model_dump(exclude_none=True))
    
    print("----- chat finished -----")
    return final_msg.content or ""


# # 流式输出到控制台
# res_str = []
# for c in call_stream(from_md("./files/input.md")):
#     res_str.append(c)
#     print(c, end='', flush=True)
#     time.sleep(0.1)

# to_md(''.join(res_str), "./files/output_buffer.md")

result = call_tools(from_md("./files/input.md"))
print(result)
to_md(result, "./files/output_buffer.md")