# 流式语音聊天系统

基于VLLM和Fish Audio的最小化流式语音对话应用。

## 🎯 功能特性

- **流式文本生成**: 使用VLLM部署的Qwen3模型进行实时文本生成
- **流式语音合成**: 使用Fish Audio WebSocket API进行实时TTS
- **简洁UI**: 基于TK的简单易用界面
- **音频播放**: 自动播放生成的语音回答

## 📁 项目结构

```
fish-speech-api/
├── src/
│   ├── config.py              # 配置文件
│   ├── core/                  # 核心功能模块
│   │   ├── vllm_stream.py     # VLLM流式客户端
│   │   ├── fish_websocket.py  # Fish Audio WebSocket客户端
│   │   ├── audio_player.py    # 音频播放器
│   │   └── stream_integration.py # 流式集成
│   └── gui/
│       └── tk_app.py          # TK界面应用
├── tests/
│   └── test_integration.py    # 集成测试
├── docs/
│   └── README.md             # 项目文档
└── requirements.txt          # 依赖文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置服务

编辑 `src/config.py`，配置你的服务地址：

```python
# VLLM 配置
VLLM_BASE_URL = "你的VLLM服务地址"
VLLM_MODEL = "Qwen3"

# Fish Audio 配置  
FISH_API_KEY = "你的Fish Audio API Key"
FISH_REFERENCE_ID = "你的音色ID"
```

### 3. 运行测试

```bash
cd fish-speech-api
python tests/test_integration.py
```

### 4. 启动应用

```bash
cd fish-speech-api/src/gui
python tk_app.py
```

## 🔧 使用方法

1. **启动应用**: 运行TK界面应用
2. **等待初始化**: 应用会自动测试服务连接
3. **输入问题**: 在输入框中输入你的问题
4. **发送**: 点击"发送并生成语音"按钮
5. **等待回答**: 系统会流式生成文本并转换为语音
6. **播放语音**: 生成完成后自动播放语音

## 📝 API接口

### VLLMStreamClient

```python
from core.vllm_stream import VLLMStreamClient

client = VLLMStreamClient()

# 流式聊天
async for chunk in client.stream_chat("你好"):
    print(chunk, end='')
```

### FishWebSocketClient  

```python
from core.fish_websocket import FishWebSocketClient

client = FishWebSocketClient()

# 简单TTS
audio_data = await client.simple_tts("你好")

# 流式TTS
async for audio_chunk in client.stream_tts(text_stream):
    # 处理音频块
    pass
```

### StreamingVoiceChat

```python
from core.stream_integration import StreamingVoiceChat

chat = StreamingVoiceChat()

# 处理语音聊天
await chat.process_voice_chat("你好", audio_callback)
```

## ⚙️ 配置说明

### VLLM配置
- `VLLM_BASE_URL`: VLLM服务地址
- `VLLM_MODEL`: 模型名称
- `VLLM_API_KEY`: API密钥（通常为"EMPTY"）

### Fish Audio配置  
- `FISH_API_KEY`: Fish Audio API密钥
- `FISH_WS_URL`: WebSocket服务地址
- `FISH_REFERENCE_ID`: 默认音色ID

### TTS配置
- `TTS_FORMAT`: 音频格式（mp3/wav）
- `TTS_LATENCY`: 延迟模式（normal/balanced）
- `TTS_TEMPERATURE`: 语音生成温度
- `TTS_TOP_P`: 语音生成top_p参数

## 🧪 测试

项目包含完整的集成测试：

```bash
python tests/test_integration.py
```

测试内容：
- VLLM服务连接测试
- VLLM流式生成测试
- Fish Audio WebSocket测试
- 完整流程集成测试

## 📋 依赖说明

- `httpx`: HTTP客户端
- `ormsgpack`: MessagePack序列化
- `openai`: OpenAI兼容客户端
- `websockets`: WebSocket客户端
- `pygame`: 音频播放
- `tkinter`: GUI界面（Python内置）

## 🎛️ 界面说明

### 主界面功能
- **输入框**: 输入你的问题
- **发送按钮**: 开始生成语音回答
- **停止按钮**: 停止音频播放
- **清空按钮**: 清空输入框
- **历史记录**: 显示对话历史
- **状态栏**: 显示当前状态

### 快捷键
- `Ctrl+Enter`: 发送消息

## 🔍 故障排除

### 常见问题

1. **VLLM连接失败**
   - 检查VLLM服务是否运行
   - 确认服务地址配置正确
   - 检查网络连接

2. **Fish Audio连接失败**
   - 检查API Key是否正确
   - 确认网络可以访问Fish Audio服务
   - 检查WebSocket连接

3. **音频播放失败**
   - 确保系统音频设备正常
   - 检查pygame是否正确安装

4. **依赖安装失败**
   - 使用Python 3.8+版本
   - 确保pip版本较新
   - 可能需要安装系统级音频依赖

## �� 许可证

本项目仅供学习和研究使用。 