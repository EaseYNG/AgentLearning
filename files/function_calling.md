你好！很高兴看到你对构建 AI Agent 的核心技术感兴趣。作为川大软工的学生，你一定对系统交互和 API 设计不陌生。**Function Calling（函数调用）** 是大语言模型从“聊天机器人”进化为“智能体（Agent）”的关键桥梁。它允许模型自主决定何时、何地以及如何调用外部工具或 API。

下面我从**原理、流程、代码实现**三个维度为你详细拆解。

### 1. 核心原理

传统模式下，模型只能输出自然文本。开启 Function Calling 后，模型被赋予了“结构化输出”的能力。通过预定义的 **JSON Schema**，模型可以在回复中生成包含特定函数名和参数的对象，而不是直接编造答案。这解决了模型无法实时访问数据（如天气、数据库、API）的问题。

### 2. 标准工作流（The Loop）

构建一个支持 Function Calling 的 Agent 通常包含以下四步循环：

1.  **定义工具（Define Tools）**：在请求参数 `tools` 中声明可用函数的名称、描述及参数 Schema。
2.  **模型决策（Model Decision）**：用户发送 Prompt，模型判断是否需要调用工具。如果需要，返回格式化的 `tool_calls` 字段；否则直接输出文本。
3.  **执行与回传（Execute & Return）**：**注意！这是后端逻辑**。你的代码解析出模型想要调用的函数，实际执行该 Python 函数（如查询数据库），然后将结果追加到对话历史中。
4.  **生成最终回复（Generate Response）**：再次将更新后的历史记录发给模型，让模型根据工具返回的实际结果组织语言回答用户。

### 3. tools 结构

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

### 4. response 结构

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

### 5. message 结构

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

其中content和tool_calls是互斥的。

### 6. Python 代码示例

基于 `openai` 官方库，以下是简化版演示：

```python
from openai import OpenAI
import json

client = OpenAI(api_key="YOUR_API_KEY")

# 1. 定义工具函数
def get_current_weather(location, unit='celsius'):
    """模拟获取天气"""
    print(f"调用外部接口获取 {location} 的天气...")
    return f"{location}: 晴朗，25{unit}"

# 2. 构造请求结构
tools = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "获取指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
}]

# 3. 发起第一次请求（假设模型决定调用函数）
response = client.chat.completions.create(
    model="gpt-4o-mini", # 推荐使用最新模型
    messages=[{"role": "user", "content": "成都明天天气如何？"}],
    tools=tools,
    tool_choice="auto" # 自动决定是否调用
)

if response.choices[0].message.tool_calls:
    # 4. 解析并执行真实函数
    tool_call_id = response.choices[0].message.tool_calls[0].id
    func_name = response.choices[0].message.tool_calls[0].function.name
    args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)

    result = eval(func_name)(**args) # 实际开发请避免 eval，用动态导入

    # 5. 构建第二次请求（提交工具结果）
    messages = response.choices[0].message.to_dict()
    messages['tool_calls'][0]['function']['arguments'] = result # 简化处理，实际需加 role: tool

    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    print(final_response.choices[0].message.content)
```
