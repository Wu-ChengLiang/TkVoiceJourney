# Fish Audio TTS 集成

基于 [Fish Audio 官方文档](https://docs.fish.audio/introduction) 的文本转语音(TTS)服务集成。

## 📋 功能特性

- ✅ 支持 SDK 和 Raw API 两种调用方式
- ✅ 支持多种 TTS 模型 (`speech-1.5`, `speech-1.6`, `s1`, `s1-mini`)
- ✅ 支持参考音频进行声音克隆
- ✅ 支持多种音频格式 (MP3, WAV, PCM)
- ✅ 支持不同音质设置
- ✅ 完善的错误处理和日志
- ✅ 中英文混合支持

## 🛠️ 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install httpx ormsgpack pydantic fish-audio-sdk
```

## 🔑 API 配置

API Key 已经配置在代码中：`c519c7c1b9a249069c078110c9ed4af9`

## 📁 文件说明

- `fish_tts_client.py` - 完整的 TTS 客户端类（推荐使用）
- `api.py` - 改进的基础 API 调用示例
- `example_usage.py` - 详细使用示例
- `requirements.txt` - 依赖文件

## 🚀 快速开始

### 方式1：使用 TTS 客户端类（推荐）

```python
from fish_tts_client import FishTTSClient

# 初始化客户端
client = FishTTSClient()

# 基本文本转语音
success = client.tts(
    text="你好世界！欢迎使用Fish Audio。",
    output_file="output.mp3",
    model="s1-mini"
)
```

### 方式2：使用基础 API

```python
from api import text_to_speech

# 调用TTS
success = text_to_speech(
    text="Hello, world!",
    output_file="hello.mp3",
    model="speech-1.5"
)
```

## 🎵 使用示例

### 1. 基本文本转语音

```python
client = FishTTSClient()

# 中文
client.tts("你好世界", "chinese.mp3")

# 英文  
client.tts("Hello world", "english.mp3")
```

### 2. 使用不同模型

```python
models = ["speech-1.5", "speech-1.6", "s1", "s1-mini"]

for model in models:
    client.tts(
        text=f"这是{model}模型的测试",
        output_file=f"test_{model}.mp3",
        model=model
    )
```

### 3. 使用参考音频进行声音克隆

```python
# 需要有参考音频文件
client.tts(
    text="这是声音克隆的测试",
    output_file="cloned_voice.mp3",
    use_sdk=False,  # Raw API 支持参考音频
    reference_audio=("reference.wav", "参考音频的文本"),
    model="speech-1.5"
)
```

### 4. 不同音频格式

```python
# MP3 格式
client.tts(
    text="MP3格式测试",
    output_file="test.mp3",
    use_sdk=False,
    format="mp3",
    mp3_bitrate=192
)

# WAV 格式
client.tts(
    text="WAV格式测试", 
    output_file="test.wav",
    use_sdk=False,
    format="wav"
)
```

### 5. 使用参考模型ID

```python
# 从 Fish Audio Playground 获取模型ID
client.tts(
    text="使用预训练模型",
    output_file="model_voice.mp3",
    reference_id="7f92f8afb8ec43bf81429cc1c9199cb1"
)
```

## 🔧 可用参数

### TTS 模型
- `speech-1.5` - 标准模型
- `speech-1.6` - 改进模型  
- `s1` - 高质量模型
- `s1-mini` - 轻量级模型（推荐）

### 音频格式
- `mp3` - MP3格式 (默认)
- `wav` - WAV格式
- `pcm` - PCM格式

### MP3 比特率
- `64` - 低质量
- `128` - 标准质量 (默认)
- `192` - 高质量

### 延迟模式
- `normal` - 正常延迟 (默认)
- `balanced` - 平衡模式 (300ms延迟)

## 🏃‍♂️ 运行示例

```bash
# 运行完整测试示例
python example_usage.py

# 运行基础API测试
python api.py

# 运行客户端类测试
python fish_tts_client.py
```

## 📊 API 限制

根据 [Fish Audio 文档](https://docs.fish.audio/introduction)：

- 请查看官方的 Rate Limits 页面了解具体限制
- 建议加入 Developer Program 获得更好的支持

## 🔗 相关链接

- [Fish Audio 官方文档](https://docs.fish.audio/introduction)
- [TTS API 文档](https://docs.fish.audio/text-to-speech/text-to-speech)
- [Fish Audio Playground](https://fish.audio/)
- [Python SDK GitHub](https://github.com/fishaudio/fish-audio-sdk)

## ⚠️ 注意事项

1. **API Key 安全**：生产环境中应使用环境变量存储 API Key
2. **文件路径**：确保输出路径有写入权限
3. **参考音频**：使用参考音频时确保文件存在且格式正确
4. **网络连接**：确保网络连接稳定，TTS 请求可能需要一些时间
5. **错误处理**：建议在实际应用中添加重试机制

## 🎯 最佳实践

1. **优先使用 SDK**：SDK 提供更好的错误处理和功能
2. **选择合适模型**：`s1-mini` 适合大多数场景，速度快质量好
3. **音频格式选择**：MP3 适合存储，WAV 适合后续处理
4. **参考音频质量**：使用高质量、清晰的参考音频效果更好
5. **批量处理**：大量文本建议分批处理避免超时 