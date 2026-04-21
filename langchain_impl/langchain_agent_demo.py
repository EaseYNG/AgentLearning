import os
from typing import List, Dict
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from pydantic import BaseModel


API_KEY = os.getenv("ALIYUN_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
base_dir = os.path.dirname(__file__)

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

llm = ChatOpenAI(
    model="qwen3.5-397b-a17b",
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL
)

# db_schema definition
class Column(BaseModel):
    name: str
    type: str
class Table(BaseModel):
    name: str
    columns: List[Column]
    description: str
class DBSchema(BaseModel):
    tables: List[Table]

# tools definition

@tool
def get_weather(city: str) -> str:
    '''获取某城市天气
    Args:
        city: 城市名
    '''
    return f"The weather in {city} is sunny."

@tool
def get_activity(weather: str) -> str:
    '''根据天气推荐活动
    Args:
        weather: 天气情况
    '''
    if weather == "sunny":
        return "play football"
    elif weather == "rainy":
        return "stay at home"
    
@tool
def notice(activity: str) -> str:
    '''根据活动给出注意事项
    Args:
        activity: 活动名
    '''
    if activity == "stay at home":
        return "have a rest."
    if activity == "play football":
        return "safety first!"
    
tools = [get_weather, get_activity, notice]

# 工具调用错误
@wrap_tool_call
def tool_call_error_handler(request, handler):
    '''工具调用错误处理'''
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"tool call error: {str(e)}",
            tool_call_id=request.tool_call["id"]
        )
    
# 创建agent
agt = create_agent(
    model=llm,
    tools=tools,
    middleware=[tool_call_error_handler],
)

def generate_prompt(message: str):
    pass # TODO: 构建适当的prompt模板

def call(message: List[str]):
    _messages = []
    for m in message:
        _messages.append(HumanMessage(m))

    print("----- start agent -----")
    # 调用agent
    try:
        response = agt.invoke(
            {"messages": _messages}
        )
    except Exception as e:
        print(f"对话请求失败：{e}")
        raise
    finally:
        print("----- end agent -----")
    
    result = response["messages"]
    # response.messages 包含全部对话历史
    if isinstance(result, list):
        # 倒序遍历，通常能找到最终回复
        for m in reversed(result):
            if isinstance(m, AIMessage):
                return m.content
        return ""
    if isinstance(result, AIMessage):
        return result.content

def call_chain(template: ChatPromptTemplate, input_dict: Dict) -> str:
    '''
    Args:
        template: 提示词模板
        input_dict: 包含提示词模板中输入参数的字典
    '''
    chain = template | llm
    print("----- start chain -----")
    try:
        response = chain.invoke(input=input_dict)
    except Exception as e:
        print(e)
        raise
    finally:
        print("----- end chain -----")

    return response.content
   


def main():
    # 定义输入模型
    sch = DBSchema(
        tables=[
            Table(
                name="user",
                columns=[
                    Column(
                        name="id",
                        type="BIGINT"
                    ),
                    Column(
                        name="username",
                        type="str"
                    ),
                    Column(
                        name="password",
                        type="str"
                    )
                ],
                description="用户表"
            ),
            Table(
                name="activity",
                columns=[
                    Column(
                        name="id",
                        type="BIGINT"
                    ),
                    Column(
                        name="title",
                        type="str"
                    ),
                    Column(
                        name="description",
                        type="str"
                    )
                ],
                description="活动表"
            ),
            Table(
                name="activity_participant",
                columns=[
                    Column(
                        name="id",
                        type="BIGINT"
                    ),
                    Column(
                        name="activity_id",
                        type="BIGINT"
                    ),
                    Column(
                        name="participant_id",
                        type="BIGINT"
                    )
                ],
                description="用户-活动参与记录表，其中activity_id引用activity表的id，participant_id引用user表的id"
            )
        ]
    )

    # prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", '''
            # 角色设定
            {system_message}
            # 任务
            请根据输入的数据库schema、键引用关系，理解表间关系，分别为输入的表生成指定数量条元组，按json列表格式输出（键为列名，值为对应的值）,
            额外要求为 {extra}.
            # 输出格式
            列表，取决于输入的schema元素个数，每个列表的元素是一个字典，包含各列对应的值。'''),
        ("user", '''
            {schema} - 数据库schema，包含表名和列名
            {count} - 要生成的元组个数
            {extra} - 额外要求（比如可能存在的外键依赖、某些属性的域等）''')
    ])

    input_dict = {
            "system_message": "你是一位SQL专家，能够精准捕捉数据间的关系",
            "schema": sch.model_dump(),
            "count": 10,
            "extra": "生成与现实高度相关的数据，user的密码统一设置为'password123'"
    }
    res_str = call_chain(prompt_template, input_dict)
    print(res_str)
    to_md(res_str, os.path.join(base_dir, "files", "output_buffer.md"))

if __name__ == "__main__":
    main()