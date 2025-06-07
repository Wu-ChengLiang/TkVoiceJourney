# TkVoiceJourney - OpenAI兼容的Fish Audio TTS系统

🎵 一个完全兼容OpenAI API的语音合成和对话系统，基于Fish Audio TTS和多种LLM后端。

## ✨ 特性

- 🔄 **OpenAI API 完全兼容** - 像使用OpenAI SDK一样简单
- 🎯 **一键切换LLM后端** - 支持OpenAI和vLLM无缝切换
- 🎵 **高质量TTS** - 基于Fish Audio的实时语音合成
- 🔐 **安全配置** - 通过.env文件管理所有密钥，代码中不暴露
- 🌊 **流式处理** - 支持实时流式对话和TTS生成
- 🎭 **集成功能** - 流式对话+实时TTS一体化

## 🚀 快速开始

### 1. 环境配置

克隆项目后，在根目录创建 `.env` 文件：

```bash
# 复制示例配置
cp .env.example .env
```

编辑 `.env` 文件：

```env
# ===========================================
# TkVoiceJourney 环境配置文件
# ===========================================

# ==================== LLM配置 ====================
# 当前使用模式：可选择 "openai" 或 "vllm"
LLM_MODE=openai

# OpenAI 配置
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# VLLM 配置
VLLM_BASE_URL=https://your-vllm-endpoint.com/v1
VLLM_API_KEY=EMPTY
VLLM_MODEL=Qwen2.5-7B-Instruct

# ==================== Fish Audio TTS配置 ====================
# Fish Audio API密钥
FISH_API_KEY=your_fish_api_key_here

# Fish Audio WebSocket URL
FISH_WS_URL=wss://api.fish.audio/v1/tts/live

# Fish Audio参考音色ID（从playground获取）
FISH_REFERENCE_ID=your_reference_id_here

# TTS参数配置
TTS_FORMAT=mp3
TTS_LATENCY=normal
TTS_TEMPERATURE=0.7
TTS_TOP_P=0.7
TTS_BACKEND=speech-1.6
```

### 2. 获取API密钥

#### Fish Audio 配置
1. 访问 [Fish Audio](https://fish.audio)
2. 注册账户并获取API Key
3. 在Playground中选择或创建音色，获取Reference ID

#### OpenAI 配置（如果使用OpenAI模式）
1. 访问 [OpenAI Platform](https://platform.openai.com)
2. 获取API Key

#### vLLM 配置（如果使用vLLM模式）
1. 部署vLLM服务
2. 配置Base URL和模型名称

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行示例

```bash
# 运行完整示例
python examples/openai_usage_example.py

# 测试配置
python src/config.py

# 测试LLM连接
python src/core/vllm_stream.py

# 测试Fish Audio TTS
python src/core/fish_websocket.py
```

## 📖 使用方法

### OpenAI兼容API

完全按照OpenAI SDK的方式使用：

```python
from src.core.openai_compatible import OpenAI

# 创建客户端
client = OpenAI()

# 聊天完成
response = await client.chat.create(
    messages=[
        {"role": "system", "content": "你是一个友好的助手"},
        {"role": "user", "content": "你好"}
    ],
    stream=False
)

# 流式聊天
stream = await client.chat.create(
    messages=[{"role": "user", "content": "介绍一下AI"}],
    stream=True
)

async for chunk in stream:
    if chunk['choices'][0]['delta'].get('content'):
        print(chunk['choices'][0]['delta']['content'], end="")

# 文本转语音
audio_data = await client.audio.speech.create(
    model="tts-1",
    input="你好，这是测试音频",
    voice="alloy",
    response_format="mp3"
)

with open("output.mp3", "wb") as f:
    f.write(audio_data)
```

### 集成流式对话+TTS

```python
from src.core.openai_compatible import OpenAICompatibleClient

client = OpenAICompatibleClient()

# 流式对话+实时TTS
stream = client.stream_chat_with_tts(
    user_input="介绍一下Python",
    system_prompt="你是一个技术专家",
    enable_tts=True
)

async for chunk in stream:
    if chunk['type'] == 'text':
        print(chunk['content'], end="")
    elif chunk['type'] == 'audio':
        # 处理音频数据
        audio_data = base64.b64decode(chunk['content'])
        # 保存或播放音频
```

## 🔄 LLM模式切换

### 切换到OpenAI模式

编辑 `.env` 文件：

```env
LLM_MODE=openai
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 切换到vLLM模式

编辑 `.env` 文件：

```env
LLM_MODE=vllm
VLLM_BASE_URL=https://your-vllm-endpoint.com/v1
VLLM_API_KEY=EMPTY
VLLM_MODEL=Qwen2.5-7B-Instruct
```

重启应用即可自动切换。

## 🏗️ 项目结构

```
fish-speech-api/
├── .env                          # 环境配置文件（根目录）
├── requirements.txt              # 依赖包列表
├── README.md                     # 项目说明
├── examples/
│   └── openai_usage_example.py   # OpenAI兼容API使用示例
└── src/
    ├── config.py                 # 配置管理
    └── core/
        ├── vllm_stream.py        # 统一LLM客户端
        ├── fish_websocket.py     # Fish Audio WebSocket客户端
        ├── openai_compatible.py  # OpenAI兼容API封装
        └── audio_player.py       # 音频播放器
```

## 🔧 配置参数说明

### LLM配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `LLM_MODE` | LLM模式 (`openai` 或 `vllm`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `OPENAI_BASE_URL` | OpenAI API地址 | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI模型名称 | `gpt-4o-mini` |
| `VLLM_BASE_URL` | vLLM服务地址 | - |
| `VLLM_API_KEY` | vLLM API密钥 | `EMPTY` |
| `VLLM_MODEL` | vLLM模型名称 | `Qwen2.5-7B-Instruct` |

### Fish Audio TTS配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `FISH_API_KEY` | Fish Audio API密钥 | - |
| `FISH_WS_URL` | WebSocket地址 | `wss://api.fish.audio/v1/tts/live` |
| `FISH_REFERENCE_ID` | 音色参考ID | - |
| `TTS_FORMAT` | 音频格式 | `mp3` |
| `TTS_LATENCY` | 延迟模式 | `normal` |
| `TTS_TEMPERATURE` | 生成温度 | `0.7` |
| `TTS_TOP_P` | Top-P采样 | `0.7` |
| `TTS_BACKEND` | TTS后端模型 | `speech-1.6` |

### 应用配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `OUTPUT_DIR` | 输出目录 | `output` |
| `TEMP_DIR` | 临时目录 | `temp` |
| `DEBUG` | 调试模式 | `false` |
| `AUDIO_PLAYER_ENABLED` | 音频播放 | `true` |

## 🎯 API参考

### Chat Completions

完全兼容OpenAI Chat Completions API：

```python
# 支持的参数
await client.chat.create(
    messages=[...],           # 消息列表
    model="gpt-3.5-turbo",   # 模型名称（保持兼容）
    stream=False,            # 是否流式
    temperature=0.7,         # 温度
    max_tokens=1000,         # 最大tokens
)
```

### Audio Speech

完全兼容OpenAI Audio Speech API：

```python
# 支持的参数
await client.audio.speech.create(
    model="tts-1",           # TTS模型（保持兼容）
    input="文本内容",         # 输入文本
    voice="alloy",           # 音色（保持兼容）
    response_format="mp3",   # 响应格式
    speed=1.0                # 语速（保持兼容）
)
```

## 🧪 测试

```bash
# 运行所有测试
python examples/openai_usage_example.py

# 测试特定组件
python src/core/vllm_stream.py
python src/core/fish_websocket.py
python src/core/openai_compatible.py

# 检查配置
python src/config.py
```

## 🔍 故障排除

### 常见问题

1. **连接失败**
   - 检查 `.env` 文件中的API密钥是否正确
   - 确认网络连接正常
   - 验证Fish Audio余额是否充足

2. **音频生成失败**
   - 确认Fish Audio API Key和Reference ID正确
   - 检查文本内容是否符合要求

3. **LLM响应异常**
   - 验证LLM模式配置
   - 检查对应的API密钥和地址

### 健康检查

```python
from src.core.openai_compatible import OpenAICompatibleClient

client = OpenAICompatibleClient()
health = await client.health_check()
print(health)
```

## 📝 更新日志

### v1.0.0
- ✅ OpenAI API完全兼容
- ✅ 支持OpenAI和vLLM切换
- ✅ Fish Audio TTS集成
- ✅ 流式对话+TTS
- ✅ 安全的环境配置

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Fish Audio 官网](https://fish.audio)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [vLLM 项目](https://github.com/vllm-project/vllm) 