在 LangChain 中，`agent.invoke()` 的返回结果**并不是固定不变的字典结构**。它的返回类型完全取决于你使用的 **Agent 类型**以及最终配置的 **Output Parser（输出解析器）**。

然而，为了满足你对“字典结构”的需求，通常开发者会包装一个结构化输出或配置了特定的输出解析器（例如 Pydantic Model）。以下我将从**默认行为**、**常见自定义字典结构**以及**关键字段含义**三个维度详细解释。

### 1. 核心结论：返回什么取决于配置

*   **默认情况 (Default):** 如果未使用结构化输出解析器，`invoke()` 通常直接返回 **字符串 (str)** 或 **聊天消息对象 (BaseMessage)**。
*   **结构化情况 (Structured):** 如果你使用了 `RunnablePassthrough` 包装，或者配置了 Pydantic 模型作为 Output Parser，`invoke()` 才会返回一个标准的 **Python 字典 (dict)** 或 **Dict-subclass**。

以下是假设你正在处理一个**封装好的结构化 Agent 结果（返回 Dict）**时的典型字段及其含义。

### 2. 典型返回字典结构 (JSON/Python Dict)

如果你在应用层对 Agent 的输出进行了封装，最常见的返回结构如下：

```python
{
    "input": {
        "question": "string",      # 用户的原始输入 Prompt
        "chat_history": [...]      # (可选) 历史对话记录
    },
    "output": "string",           # 智能体最终的回复内容
    "intermediate_steps": [       # (可选) 中间执行步骤 (工具调用日志)
        {
            "action": "ToolName", # 调用的工具名
            "action_input": {},   # 工具输入参数
            "observation": "string" # 工具返回的观察结果
        }
    ],
    "metadata": {                 # (可选) 元数据信息
        "model_name": "gpt-4",
        "token_usage": {"prompt": 100, "completion": 50},
        "timestamp": "2023-10-27T10:00:00Z"
    }
}
```

### 3. 字段详细含义解析

| 字段名称 | 类型 | 含义说明 | 是否默认存在 |
| :--- | :--- | :--- | :--- |
| **`input`** | `Dict` / `Str` | 传入 Agent 的任务内容。如果是链式编排，可能是指传递给 Agent 的上下文变量。 | ✅ (通常作为输入传参) |
| **`output`** | `Str` / `Any` | **核心字段**。这是 Agent 经过思考、调用工具后生成的最终人类可读的答案或解析后的结构化数据。 | ✅ |
| **`intermediate_steps`** | `List[Dict]` | 记录 Agent 在执行过程中的每一步动作（如：调用计算器、搜索谷歌等）。包含动作名称、输入和观察结果。 | ❌ **(注意：默认 invoke 不返回此字段)** |
| **`reasoning`** | `Str` | (可选) 用于 CoT (思维链) 的场景，展示 AI 的思考路径，而非最终答案。 | ❌ |
| **`usage`** / **`metadata`**| `Dict` | 包含 Token 消耗量、模型版本、耗时等运维监控信息。 | ❌ |
| **`error`** / **`traceback`**| `Str` / `Object` | (仅在失败时) 捕获到的异常堆栈信息，便于调试。 | ❌ |

### 4. 关键注意事项与代码实现

#### ⚠️ 重要提醒：`intermediate_steps` 的来源
在 LangChain 的原生 `Agent.invoke()` 中，**默认并不直接返回 `intermediate_steps`**。这些步骤通常保存在内部状态或由 **Callback Handler** 捕获。如果你想拿到它们，通常需要手动包装：

```python
from langchain_core.agents import AgentAction, AgentFinish
from langchain.prompts import PromptTemplate
from langchain.chains import create_react_chain
import json

# 示例：如何构建一个返回标准字典的结构
def create_structured_agent(agent_executor):
    def wrapper(inputs):
        # 1. 获取原始输出
        response = agent_executor.invoke(inputs)
        
        # 2. (模拟) 如果你想包含步骤，通常需要在创建 AgentExecutor 
        #    时配置 callbacks，然后从回调中提取，或使用 LangGraph
        
        # 3. 构造统一字典结构
        return {
            "input": inputs.get("input"),
            "output": response.content if hasattr(response, 'content') else str(response),
            # 注意：这里如果没有特定配置，steps 可能为空
            "intermediate_steps": [] 
        }
    return wrapper

# 或者使用 LangChain 更推荐的输出解析器 (Pydantic)
from pydantic import BaseModel

class AgentResponse(BaseModel):
    answer: str
    thoughts: str
    
agent_parsed = agent | AgentResponse()
# 此时 agent_parsed.invoke(...) 将直接返回该模型序列化为字典的结果
```

#### 场景一：默认返回 (String)
大多数教程中的 `AgentExecutor` 默认用法：
```python
result = agent.invoke({"input": "计算 2+2"})
print(type(result))  # <class 'str'>
# 没有 fields，只有纯文本
```

#### 场景二：LangGraph 状态 (State)
如果你是在 **LangGraph** 中使用 Agent 节点，`invoke` 返回的是 **State Update (Dict)**，其结构遵循你的 State Schema：
```python
# 在 LangGraph 中
class GraphState(TypedDict):
    input: str
    output: str
    steps: list

# Node 返回的 Dict 将更新此 State
return {"output": generated_text, "steps": current_steps}
```

### 总结
1.  **LangChain `invoke()` 的核心是输出解析器的产物。** 不要指望它自动返回包含 `steps` 的字典。
2.  **若需字典结构**，请使用 **Pydantic BaseModels** 配合 **Runnable`output_parser`** 或在外部封装一个返回 `Dict` 的函数。
3.  **获取执行步骤**：建议通过配置 **LangSmith Callbacks** 追踪执行路径，或在 Agent 初始化时传入自定义的 Handler 来收集 `intermediate_steps`。