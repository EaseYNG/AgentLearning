from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
import os
from typing import List, Dict

# 常量定义
API_KEY = os.getenv("ALIYUN_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
base_dir = os.path.dirname(__file__) # 当前文件所在路径

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

# tools declaration
@tool
def get_weather(city: str) -> str:
    '''根据城市名获取天气
    
    Args:
        city: 要查询天气的城市
    '''
    return f"The weather in {city} is sunny."

@tool
def recommend_activity(weather: str) -> str:
    '''根据天气推荐活动
    Args:
        weather: 要查询对应推荐活动的天气
    '''
    if weather == 'sunny':
        return "It's time to go outside!"

@tool
def notice(activity: str) -> str:
    '''提供活动的注意事项
    Args:
        activity: 要提供对应注意事项的活动
    '''
    return f"[{activity}] safety first!"

tools = [get_weather, recommend_activity, notice]

TOOL_MAP = {tool.name: tool for tool in tools}

def func_calling(system_message, user_message, tools: List):
    '''带工具调用的langchain示例
    记得维护完整的消息列表
    '''
    model = ChatOpenAI(
        model="qwen3.5-397b-a17b",
        openai_api_key=API_KEY,
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    model_with_tools = model.bind_tools(tools)

    sys_msg = SystemMessage(system_message)
    user_msg = HumanMessage(user_message)

    messages = [
        sys_msg,
        user_msg
    ]
    
    # 循环直至工具链式调用完毕
    while True:
        ai_msg = model_with_tools.invoke(messages)
        # 维护对话历史
        messages.append(ai_msg)
        for tool_call in ai_msg.tool_calls:
            # 执行方法
            selected_tool = TOOL_MAP[tool_call["name"]]
            args = tool_call["args"]
            id = tool_call["id"]
            # 调用方法、传回模型
            tool_result = selected_tool.invoke(args)
            # 构建tool message
            # 调用id和调用结果
            tool_msg = ToolMessage(
                tool_call_id=id,
                content = tool_result
            )
            # 维护对话历史
            messages.append(tool_msg)
        
        # 工具调用为空，说明已调用完成，或从未调用工具，跳出循环
        if not ai_msg.tool_calls:
            to_md(str(ai_msg.content), os.path.join(base_dir, "files", "output_buffer.md"))
            print(ai_msg.content)
            break

def main():
    func_calling("",
                 "获取兰州市天气，推荐活动，并给出注意事项",
                 tools=tools)
    
if __name__ == "__main__":
    main()


