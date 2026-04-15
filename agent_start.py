import os
from datetime import datetime
from openai import OpenAI
import time
import json
from history_manager import HistoryManager

def to_md(message, file_name):
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(message)
    except FileNotFoundError:
        print("文件不存在")
    except Exception as e:
        print(f"错误：{e}")

def from_md(file_name) -> str:
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("文件不存在")
    except Exception as e:
        print(f"错误：{e}")
    
def append_md(message, file_name):
    try:
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(message)
    except FileNotFoundError:
        print("文件不存在")
    except Exception as e:
        print(f"错误：{e}")

# 初始化对话历史管理器
chat_history = HistoryManager()

# 定义客户端
client = OpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 调用api（非流式&流式）
def call(message, model="qwen3.5-flash"):
    '''非流式chat'''
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
    chat_history.update()
    print("----- chat finished -----")
    return response.choices[0].message.content

def call_stream(message, model="qwen3.5-flash"):
    '''流式chat生成器：不断生成流式输出块'''
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
    chat_history.update()
    print()
    print("----- chat finished -----")

# function calling
def get_weather(city: str):
    return f"The weather in {city} is rainy."

def recommend_activity(weather: str):
    if weather == 'sunny':
        return "It's time to go outside!"
    elif weather == 'rainy':
        return "stay at home!"

def notice(activity: str):
    return "safety first!"

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
    {
        "type": "function",
        "function" : {
            "name": "recommend_activity",
            "description": "根据天气情况获取推荐的活动",
            "parameters": {
                "type": "object",
                "properties": {
                    "weather": {"type": "string", "description": "要输入的天气"},
                },
                "required": ["weather"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notice",
            "description": "根据活动提供注意事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity": {"type": "string", "description": "要输入的活动名称"}
                },
            },
            "required": "activity"
        }
    }
]

# 字符串-函数映射
FUNC_MAP = {
    "get_weather": get_weather,
    "recommend_activity": recommend_activity,
    "notice" : notice,
}

def call_tools(message: str, model="qwen3.5-flash", max_iters=10):
    '''非流式chat
    使用工具的调用'''
    
    # 格式化用户输入
    system_message = {"role": "system", "content": "你是一位精通agent开发的工程师"}
    user_message = {"role": "user", "content": message}
    chat_history.add(system_message)
    chat_history.add(user_message)

    msg = None
    
    print("----- start chat -----")
    iter = 0
    while iter < max_iters:
        response = client.chat.completions.create(
            model=model,
            tool_choice="auto",
            tools=tools,
            messages=chat_history.get()
        )

        # 获取response
        msg = response.choices[0].message
        # 加入对话历史
        chat_history.add(msg.model_dump())
        # 判断是否调用工具
        if msg.tool_calls:
            # 获取tool_calls列表
            tool_calls = msg.tool_calls
            # 处理每一次工具调用
            for call in tool_calls:
                tool_call_id = call.id
                func_name = call.function.name
                # 注意arguments为json字符串，需转换为dict
                func_args = json.loads(call.function.arguments)

                # 执行对应方法
                result = FUNC_MAP[func_name](**func_args)
                # 构造对应的tool message并加入对话历史
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(result)
                }
                chat_history.add(tool_msg)
                # 继续循环至下一次对话，直到不再调用工具
                iter += 1
        # 不再调用tools时跳出循环
        else:
            break
    
    chat_history.update()
    print("----- end chat -----")
    return msg.content

# # --------------------------------------------------
# # 流式输出测试
# res_str = []
# for c in call_stream(from_md("./files/input.md")):
#     res_str.append(c)
#     print(c, end='', flush=True)
#     time.sleep(0.1)

# to_md(''.join(res_str), "./files/output_buffer.md")
# # --------------------------------------------------

# --------------------------------------------------
# function calling test
result = call_tools(from_md("./files/input.md"))
print(result)
to_md(result, "./files/output_buffer.md")
# --------------------------------------------------