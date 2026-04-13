## function calling (openai)

### 1. 核心原理

传统模式下，模型只能输出自然文本。开启 Function Calling 后，模型被赋予了“结构化输出”的能力。通过预定义的 **JSON Schema**，模型可以在回复中生成包含特定函数名和参数的对象，而不是直接编造答案。这解决了模型无法实时访问数据（如天气、数据库、API）的问题。

### 2. 标准工作流（The Loop）

构建一个支持 Function Calling 的 Agent 通常包含以下四步循环：

1.  **定义工具（Define Tools）**：在请求参数 `tools` 中声明可用函数的名称、描述及参数 Schema。
2.  **模型决策（Model Decision）**：用户发送 Prompt，模型判断是否需要调用工具。如果需要，返回格式化的 `tool_calls` 字段；否则直接输出文本。
3.  **执行与回传（Execute & Return）**：**注意！这是后端逻辑**。你的代码解析出模型想要调用的函数，实际执行该 Python 函数（如查询数据库），然后将结果追加到对话历史中。
4.  **生成最终回复（Generate Response）**：再次将更新后的历史记录发给模型，让模型根据工具返回的实际结果组织语言回答用户。

### 3. response 结构

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1699...,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {       // <-- 这里是你要分析的 message 对象
         "role": "assistant",
         "content": null,
         "tool_calls": [...],
         "function_call": null,
         "refusal": null,
         "name": null
      },
      "finish_reason": "tool_calls", // ⚠️ 注意：这个不在 message 里，在 choice 里
      "logprobs": ...
    }
  ]
}
```

### 4. message 结构

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_8Xj9K2mL...aBcD", // ⚠️ 关键：唯一 ID，用于绑定结果
      "type": "function", // 固定值为 "function"
      "function": {
        "name": "fast_pow", // 调用的函数名
        "arguments": "{\"a\": 2, \"n\": 258}" // ⚠️ 注意：这是一个 JSON 字符串，需要二次 json.loads()
      }
    }
    // 如果有多个工具同时被调用，这里是数组会有多个对象
  ]
}
```

### 5. tools 结构

```python
tools: List [
    {
        "type": "function",
        "name": "{function_name}",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "..."}
            },
            "required": ["..."],
        },
    },
]
```

### 6. 注意事项

1. client.chat.completion.create()返回的是一个Pydantic模型，必须通过model_dump()进行json序列化
2. 在工具调用前后的两次请求间，必须传入完整的对话历史（第二次请求要手动传入role为tool的message，包含"tool_call_id"字段和"content"（返回值）
3. tool_calls列表项的function.arguments是一个json字符串，需要手动json.loads()获取json

### 7. Python 代码示例

```python
'''定义tools方法'''
def get_weather(city: str):
    return f"The weather in {city} is sunny."

def recommend_activity(weather: str):
    if weather == 'sunny':
        return "It's time to go outside!"

def notice(activity: str):
    return "safety first!"

'''创建tools字典列表'''
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

'''创建字符串-方法映射（用于调用方法）'''
FUNC_MAP = {
    "get_weather": get_weather,
    "recommend_activity": recommend_activity,
    "notice" : notice,
}

'''调用'''
def call_tools(message: str, model="deepseek-chat", max_iters=10):
    '''非流式chat
    使用工具的调用'''
    chat_history = History()

    # 格式化用户输入
    user_message = {"role": "user", "content": message}
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
                # 注意arguments为json字符串
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
    
    print("----- end chat -----")
    return msg.content
```