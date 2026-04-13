# from langchain.agents import create_agent
# from langchain_openai import ChatOpenAI
# from langchain.tools import tool
# from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
# import os

# # 常量定义
# API_KEY = os.getenv("ALIYUN_API_KEY")
# BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# def to_md(message, file_name):
#     with open(file_name, "w", encoding="utf-8") as f:
#         f.write(message)

# def from_md(file_name) -> str:
#     with open(file_name, "r", encoding="utf-8") as f:
#         return f.read()
    
# def append_md(message, file_name):
#     with open(file_name, "a", encoding="utf-8") as f:
#         f.write(message)

# # 对话历史
# class History:
#     def __init__(self):
#         os.makedirs("files", exist_ok=True)
#         self.load()

#     def load(self):
#         import json
#         try:
#             with open("files/chat_history.json", "r", encoding="utf-8") as f:
#                 self.history = json.load(f)
#         except FileNotFoundError:
#             self.history = []
    
#     # 处理好message为字典
#     def add(self, message):
#         self.history.append(message)
        
#         import json
#         with open("files/chat_history.json", "w", encoding="utf-8") as f:
#             if isinstance(message, str):
#                 json.dump(self.history, f, ensure_ascii=False, indent=2)
#             else:
#                 f.write(message)
    
#     def get(self) -> list:
#         return self.history
    
#     def clear(self):
#         self.history = []
        
#         import json
#         with open("files/chat_history.json", "w", encoding="utf-8") as f:
#             json.dump(self.history, f, ensure_ascii=False, indent=2)

# # function calling
# @tool
# def get_weather(city: str) -> str:
#     '''根据城市名获取天气'''
#     return f"The weather in {city} is sunny."

# @tool
# def recommend_activity(weather: str) -> str:
#     '''根据天气推荐活动'''
#     if weather == 'sunny':
#         return "It's time to go outside!"

# @tool
# def notice(activity: str) -> str:
#     '''提供活动的注意事项'''
#     return "safety first!"

# tools = [get_weather, recommend_activity, notice]

# model = ChatOpenAI(
#     api_key=API_KEY,
#     base_url=BASE_URL,
#     model="qwen3.5-flash",
# )

# agent = create_agent(
#     model=model,
#     tools=tools,
# )

# def model_call(message: str):
#     chat_history = History()
#     chat_history.add(HumanMessage(message))

#     print("----- start chat -----")
#     response = model.invoke(chat_history.get())

#     print("----- end chat -----")
#     chat_history.add(response)
#     return response.content

# # def agent_call(message: str):


# res_str = model_call(from_md("./files/input.md"))
# to_md(res_str.model_dump_json(), "./files/output_buffer.md")

