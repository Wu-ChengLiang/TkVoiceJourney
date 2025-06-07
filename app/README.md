# 抖音直播弹幕语音客服系统

## 📝 项目介绍

这是一个集成了实时弹幕获取、AI智能判断和TTS语音合成的现代化Web应用系统。

### ✨ 主要功能

1. **实时弹幕获取** - 连接抖音直播间，实时获取弹幕数据
2. **智能AI判断** - 使用本地AI模型判断弹幕价值并生成回复
3. **TTS语音合成** - 基于Fish-Speech-API实现文本转语音
4. **数据可视化** - 实时显示弹幕统计和分析数据
5. **Web界面** - 现代化的响应式Web界面

### 🏗️ 技术架构

- **前端**: HTML + TailwindCSS + JavaScript
- **后端**: FastAPI + WebSocket + 异步编程
- **AI模型**: Qwen + LoRA微调 + 4bit量化
- **TTS**: Fish-Speech-API
- **弹幕获取**: 抖音直播WebSocket协议

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- CUDA 支持的GPU (推荐RTX 4060 8GB+)
- 16GB+ 系统内存

### 2. 安装依赖

```bash
# 进入app目录
cd app

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 配置模型

确保以下模型文件存在：
- 基础模型: `../my_models/` 或 `../qwen3_models/`
- LoRA模型: `../qwen3_output/v10-20250530-074122/checkpoint-33/`

### 4. 启动应用

#### 方式1: 使用启动脚本
```bash
python run.py
```

#### 方式2: 直接启动
```bash
python main.py
```

#### 方式3: 测试模式(模拟弹幕)
```bash
# 修改main.py，在顶部添加：
# from test_barrage import use_test_fetcher
# use_test_fetcher()

python main.py
```

### 5. 访问系统

打开浏览器访问: http://localhost:8000

## 🎯 使用指南

### 基本操作

1. **输入直播间ID** - 在顶部输入框输入抖音直播间ID (如: 37002227641)
2. **开始监控** - 点击"弹幕获取"按钮开始监控
3. **查看弹幕** - 左上方区域实时显示弹幕流
4. **AI回复** - 右侧显示AI自动生成的回复和语音
5. **手动回复** - 可在底部输入框手动发送回复

### 界面说明

- **左上 - 实时弹幕流**: 显示各类弹幕消息(聊天、进场、礼物等)
- **左下 - 数据分析**: 弹幕类型分布、互动统计、活跃用户
- **右侧 - AI客服**: AI自动回复、手动回复、语音播放

### 弹幕类型

- 🟦 **聊天msg**: 用户聊天消息
- 🟩 **进场msg**: 用户进入直播间
- 🟪 **礼物msg**: 用户送礼物
- 🟥 **点赞msg**: 用户点赞
- 🟨 **关注msg**: 用户关注主播
- ⬜ **统计msg**: 在线人数等统计信息

## ⚙️ 配置说明

### AI模型配置

系统会自动搜索以下路径的模型：
- `../my_models/`
- `../my_models_backup/`
- `../qwen3_models/`

### TTS配置

默认使用Fish-Speech-API，可在`tts_client.py`中修改：
- API密钥
- 模型选择 (s1-mini, speech-1.5等)
- 音频格式

### 弹幕获取配置

支持两种模式：
1. **真实模式** - 连接真实抖音直播间
2. **测试模式** - 使用模拟弹幕数据

## 📊 系统特性

### 性能优化

- **显存优化**: 4bit量化，适配8GB显存
- **异步处理**: 弹幕获取、AI推理、TTS合成并发执行
- **内存管理**: 自动清理过期数据
- **缓存机制**: 弹幕缓冲区和音频文件缓存

### 错误处理

- WebSocket自动重连
- AI模型异常恢复
- TTS服务降级
- 网络中断处理

### 数据持久化

- 弹幕数据自动保存到markdown文件
- 音频文件本地存储
- 系统运行日志记录

## 🔧 开发说明

### 目录结构

```
app/
├── main.py              # 主应用入口
├── run.py              # 启动脚本
├── requirements.txt     # Python依赖
├── barrage_fetcher.py  # 弹幕获取模块
├── ai_judge.py         # AI判断模块
├── tts_client.py       # TTS客户端
├── test_barrage.py     # 测试弹幕模块
├── templates/          # HTML模板
│   └── index.html
├── static/             # 静态文件
│   └── audio/          # 音频文件存储
└── data/               # 数据文件
    └── barrage_*.md    # 弹幕记录
```

### API端点

- `GET /` - 主页面
- `POST /api/start_live` - 开始监控直播间
- `POST /api/stop_live` - 停止监控
- `POST /api/manual_reply` - 手动回复
- `GET /api/barrage_data` - 获取弹幕数据
- `WebSocket /ws` - 实时通信

### WebSocket消息格式

```json
{
  "type": "barrage|ai_reply|manual_reply",
  "data": {...},
  "timestamp": 1234567890
}
```

## 🐛 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径
   - 确认GPU内存充足
   - 查看控制台错误信息

2. **弹幕获取失败**
   - 检查直播间ID是否正确
   - 确认网络连接正常
   - 尝试使用测试模式

3. **TTS服务异常**
   - 检查Fish-Speech-API配置
   - 确认API密钥有效
   - 查看网络连接状态

4. **WebSocket连接失败**
   - 刷新页面重试
   - 检查浏览器控制台错误
   - 确认服务器正常运行

### 调试模式

启用详细日志:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## API配置

系统现已改为使用API调用方式，大大降低了本地硬件要求。

### 支持的API类型

1. **OpenAI API** (推荐)
2. **Claude API** 
3. **vLLM本地部署**
4. **自定义API**

### 配置方法

1. 复制配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件：
```bash
# OpenAI API配置
AI_API_TYPE=openai
AI_API_KEY=sk-your-openai-api-key
AI_API_BASE=https://api.openai.com/v1
AI_MODEL_NAME=gpt-3.5-turbo
```

3. 其他API配置请参考 `.env.example` 文件

**注意**: 使用API方式无需本地模型文件，只需配置相应的API密钥。 