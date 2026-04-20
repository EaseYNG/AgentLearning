from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
import os

# 常量定义
API_KEY = os.getenv("ALIYUN_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def to_md(message, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(message)

def from_md(file_name) -> str:
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read()
    
def append_md(message, file_name):
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(message)

# tools declaration
@tool
def get_weather(city: str) -> str:
    '''根据城市名获取天气'''
    return f"The weather in {city} is sunny."

@tool
def recommend_activity(weather: str) -> str:
    '''根据天气推荐活动'''
    if weather == 'sunny':
        return "It's time to go outside!"

@tool
def notice(activity: str) -> str:
    '''提供活动的注意事项'''
    return "safety first!"

tools = [get_weather, recommend_activity, notice]

