同学你好！很高兴能为你讲解 OpenAI API 的使用。作为软件工程专业的学生，掌握这项技能对你未来的项目开发非常有帮助。我会从基础到进阶，系统地为你介绍。

## 一、OpenAI API 概述

OpenAI API 提供了多种 AI 模型接口，主要包括：
- **GPT 系列**：文本生成、对话、代码生成等
- **Embeddings**：文本向量化
- **DALL·E**：图像生成
- **Whisper**：语音转文字
- **TTS**：文字转语音

## 二、准备工作

### 1. 获取 API Key
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账号
3. 进入 API Keys 页面创建新密钥
4. **重要**：妥善保管密钥，不要泄露

### 2. 安装 SDK
```bash
# Python SDK
pip install openai

# Node.js
npm install openai
```

## 三、基础使用（Python示例）

### 1. 初始化客户端
```python
from openai import OpenAI

# 方式1：环境变量（推荐）
import os
os.environ["OPENAI_API_KEY"] = "你的API密钥"
client = OpenAI()

# 方式2：直接传入
client = OpenAI(api_key="sk-...")
```

### 2. 最简单的聊天调用
```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # 或 "gpt-4", "gpt-4-turbo"
    messages=[
        {"role": "system", "content": "你是一个编程助手"},
        {"role": "user", "content": "用Python写一个快速排序算法"}
    ],
    temperature=0.7,  # 控制随机性：0-2，越高越随机
    max_tokens=1000   # 限制生成长度
)

print(response.choices[0].message.content)
```

## 四、核心参数详解

### 1. 模型选择
```python
# 常用模型
MODELS = {
    "chat": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
    "embedding": ["text-embedding-3-small", "text-embedding-3-large"],
    "image": ["dall-e-3", "dall-e-2"],
    "audio": ["whisper-1", "tts-1"]
}
```

### 2. 消息格式（messages）
```python
messages = [
    # 系统消息 - 设定AI角色
    {"role": "system", "content": "你是一位资深软件工程师"},
    
    # 用户消息 - 用户输入
    {"role": "user", "content": "解释一下RESTful API设计原则"},
    
    # 助手消息 - AI之前的回复（用于多轮对话）
    {"role": "assistant", "content": "RESTful API有6个主要原则..."},
    
    # 用户继续提问
    {"role": "user", "content": "能举例说明吗？"}
]
```

### 3. 重要参数
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    temperature=0.7,      # 创造性：0-2，代码生成建议0.2
    top_p=0.9,           # 核采样：0-1，与temperature二选一
    max_tokens=1000,     # 最大生成token数
    n=1,                 # 生成几个回复
    stream=False,        # 是否流式输出
    stop=["\n", "###"],  # 停止序列
    presence_penalty=0,  # 话题新颖度：-2到2
    frequency_penalty=0  # 减少重复：-2到2
)
```

## 五、其他功能模块

### 1. Embeddings（文本向量化）
```python
# 生成文本向量
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="四川大学软件工程专业",
    encoding_format="float"  # 或 "base64"
)

vector = response.data[0].embedding
print(f"向量维度：{len(vector)}")
```

### 2. 图像生成（DALL·E）
```python
response = client.images.generate(
    model="dall-e-3",
    prompt="一只可爱的熊猫在写代码",
    size="1024x1024",
    quality="standard",  # 或 "hd"
    n=1
)

image_url = response.data[0].url
print(f"生成的图片：{image_url}")
```

### 3. 语音转文字（Whisper）
```python
# 需要先安装：pip install pydub
from pathlib import Path

audio_file = Path("audio.mp3")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file.open("rb"),
    response_format="text"  # 或 "json", "srt", "vtt"
)
```

### 4. 文字转语音（TTS）
```python
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",  # alloy, echo, fable, onyx, nova, shimmer
    input="你好，我是AI助手"
)

# 保存音频文件
with open("output.mp3", "wb") as f:
    f.write(response.content)
```

## 六、进阶技巧

### 1. 流式输出（适合长文本）
```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "讲一个长故事"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 2. 函数调用（Function Calling）
```python
# 定义工具函数
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取城市天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    }
]

# 调用
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "成都天气怎么样？"}],
    tools=tools,
    tool_choice="auto"
)

# 解析AI返回的函数调用请求
tool_calls = response.choices[0].message.tool_calls
```

### 3. JSON模式输出
```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "列出3种排序算法"}],
    response_format={"type": "json_object"}  # 强制返回JSON
)
```

## 七、最佳实践

### 1. 错误处理
```python
from openai import OpenAIError, RateLimitError

try:
    response = client.chat.completions.create(...)
except RateLimitError:
    print("请求过快，请稍后重试")
except OpenAIError as e:
    print(f"API错误：{e}")
```

### 2. 成本控制
```python
# 估算token消耗
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(...)

# 查看使用情况
usage = response.usage
print(f"输入token: {usage.prompt_tokens}")
print(f"输出token: {usage.completion_tokens}")
print(f"总token: {usage.total_tokens}")
```

### 3. 超时设置
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    timeout=30.0,  # 30秒超时
    max_retries=3  # 重试次数
)
```

## 八、实际项目示例

### 1. 智能代码助手
```python
class CodeAssistant:
    def __init__(self):
        self.client = OpenAI()
        self.conversation_history = []
    
    def add_system_prompt(self):
        self.conversation_history.append({
            "role": "system",
            "content": """你是一个专业的代码审查助手。
            1. 分析代码问题
            2. 给出优化建议
            3. 提供改进后的代码
            4. 解释关键概念"""
        })
    
    def review_code(self, code: str, language: str = "python"):
        prompt = f"请审查以下{language}代码：\n\n{code}"
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=self.conversation_history + [
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
```

### 2. 学习助手应用
```python
class StudyAssistant:
    def __init__(self):
        self.client = OpenAI()
    
    def explain_concept(self, concept: str, level: str = "beginner"):
        """解释复杂概念"""
        prompt = f"以{level}水平解释{concept}，并举例说明"
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一位耐心的教师"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def generate_quiz(self, topic: str, num_questions: int = 5):
        """生成测验题目"""
        # 实现类似...
```

## 九、学习建议

1. **从简单开始**：先用 playground 熟悉界面
2. **理解计费**：关注 token 消耗，设置预算
3. **阅读文档**：[官方文档](https://platform.openai.com/docs/api-reference) 最权威
4. **实践项目**：
   - 命令行聊天机器人
   - 代码自动补全工具
   - 学习笔记总结助手
   - 智能客服原型

5. **关注更新**：OpenAI 经常更新模型和 API

## 十、资源推荐

1. **官方资源**：
   - [OpenAI Cookbook](https://cookbook.openai.com/)
   - [API 文档](https://platform.openai.com/docs/api-reference)
   
2. **学习平台**：
   - [OpenAI 官方课程](https://platform.openai.com/docs/quickstart)
   - Coursera/edX 相关课程

3. **社区**：
   - OpenAI Discord 社区
   - GitHub 开源项目

## 注意事项

1. **API Key 安全**：不要提交到 GitHub
2. **内容审查**：生产环境需要添加内容过滤
3. **延迟考虑**：网络请求需要时间，做好 loading 状态
4. **错误处理**：API 可能不稳定，要有重试机制

作为软件工程专业的学生，我建议你：
1. 先完成一个简单的命令行聊天工具
2. 尝试集成到你的某个课程项目中
3. 学习如何优化 prompt 获得更好结果
4. 关注 token 消耗，学习成本控制

有什么具体问题或想深入了解某个方面吗？我可以为你提供更详细的指导！