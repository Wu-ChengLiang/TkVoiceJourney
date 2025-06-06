# Qwen3-8B 微调训练指南

基于 ms-swift 框架的 Qwen3-8B 模型微调训练完整指南，优化了 8GB 显存环境下的训练流程。

## 📋 目录

- [环境准备](#环境准备)
- [数据准备](#数据准备)
- [模型准备](#模型准备)
- [训练流程](#训练流程)
- [重要参数说明](#重要参数说明)
- [模型评估](#模型评估)
- [推理部署](#推理部署)
- [常见问题](#常见问题)

## 🚀 环境准备

### 1. 系统要求

- **GPU**: NVIDIA RTX 4060 (8GB显存) 或以上
- **内存**: 16GB+ 推荐
- **存储**: 20GB+ 可用空间
- **Python**: 3.8+
- **CUDA**: 11.8 或 12.1

### 2. 安装依赖

```bash
# 安装 ms-swift 和相关依赖
pip install ms-swift[llm]

# 安装其他依赖
pip install requests tensorboard
```

### 3. 验证安装

```bash
# 检查 swift 是否正确安装
swift sft --help

# 检查 GPU 可用性
python -c "import torch; print(torch.cuda.is_available())"
```

## 📊 数据准备

### 1. 数据格式

训练数据需要转换为标准的 JSON 格式：

```json
[
  {
    "query": "用户问题",
    "response": "助手回答"
  },
  // 更多数据...
]
```

### 2. 数据文件

- **原始数据**: `./data/名医堂`
- **训练数据**: `./data/chatML.txt` (ChatML格式)

### 3. 数据质量要求

- 每条数据包含完整的问答对
- 回答符合客服助理的语气风格
- 数据量建议 100+ 条

## 🤖 模型准备

### 1. 下载 Qwen3-8B 基础模型

```bash
# 使用 Hugging Face Hub
huggingface-cli download Qwen/Qwen3-8B --local-dir ../my_models

# 或使用 Git LFS
git clone https://huggingface.co/Qwen/Qwen3-8B ../my_models
```

### 2. 验证模型文件

模型目录应包含以下文件：
- `config.json`
- `model-*-of-*.safetensors` (模型权重分片)
- `tokenizer.json`
- `tokenizer_config.json`

## 🏋️ 训练流程

### 1. 快速开始

```bash
# 运行训练脚本
python local_train_8b.py

如果显存不够 
python local_train_8b_save.py

如果遇到评估阶段错误
python local_train_8b_safe.py
```

### 2. 完整训练命令

```bash
swift sft \
  --model ../my_models \
  --model_type qwen3 \
  --dataset ./data/clean_train.json \
  --template qwen3 \
  --output_dir ./qwen3_output \
  --num_train_epochs 3 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 3e-6 \
  --max_length 1024 \
  --logging_steps 1 \
  --save_steps 100 \
  --eval_steps 100 \
  --eval_strategy steps \
  --lora_rank 64 \
  --lora_alpha 128 \
  --lora_dropout 0.05 \
  --gradient_checkpointing true \
  --quant_method bnb \
  --quant_bits 4 \
  --bnb_4bit_compute_dtype bfloat16 \
  --bnb_4bit_quant_type nf4 \
  --bnb_4bit_use_double_quant true \
  --device_map auto
```

### 3. 监控训练过程

```bash
# 查看训练日志
tensorboard --logdir ./qwen3_output

# 实时查看日志
tail -f ./qwen3_output/*/logging.jsonl
```

## ⚙️ 重要参数说明

### 核心训练参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `model_type` | `qwen3` | 模型类型，必须使用 qwen3 |
| `template` | `qwen3` | 聊天模板格式 |
| `learning_rate` | `3e-6` | 学习率，8B模型适用 |
| `num_train_epochs` | `3` | 训练轮数 |
| `max_length` | `1024` | 最大序列长度 |

### 显存优化参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `per_device_train_batch_size` | `1` | 单设备批次大小 |
| `gradient_accumulation_steps` | `16` | 梯度累积步数 |
| `quant_bits` | `4` | 4bit量化，节省显存 |
| `gradient_checkpointing` | `true` | 梯度检查点 |
| `device_map` | `auto` | 自动设备映射 |

### LoRA 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `lora_rank` | `64` | LoRA 秩，影响参数量 |
| `lora_alpha` | `128` | LoRA 缩放参数 |
| `lora_dropout` | `0.05` | LoRA Dropout率 |

### 量化参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `quant_method` | `bnb` | 使用 BitsAndBytes 量化 |
| `bnb_4bit_compute_dtype` | `bfloat16` | 计算数据类型 |
| `bnb_4bit_quant_type` | `nf4` | 量化类型 |
| `bnb_4bit_use_double_quant` | `true` | 双重量化 |

## 📈 模型评估

### 1. 自动化测试

```bash
# 运行自动化测试脚本
python model_test.py

# 或指定配置文件
python model_test.py --config models_config.json
```

### 2. 手动推理测试

```bash
# 启动推理服务
swift deploy \
  --model ./qwen3_output/checkpoint-XXX \
  --model_type qwen3 \
  --template qwen3 \
  --port 8000

# 测试API
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3",
    "messages": [
      {"role": "system", "content": "你是名医堂的客服助理"},
      {"role": "user", "content": "你们营业到几点？"}
    ],
    "max_tokens": 256
  }'
```

### 3. 评估指标

- **主观评分**: 1-5分制人工评估
- **响应速度**: 推理时间统计
- **答案质量**: 专业性、准确性、语气
- **一致性**: 多次查询结果的稳定性

## 🚀 推理部署

### 1. 本地部署

```bash
# 部署微调后的模型
swift deploy \
  --model ./qwen3_output/checkpoint-best \
  --model_type qwen3 \
  --template qwen3 \
  --port 8000 \
  --quant_method bnb \
  --quant_bits 4
```

### 2. 生产环境

```bash
# 使用 vllm 进行高性能推理
vllm serve ./qwen3_output/checkpoint-best \
  --model qwen3 \
  --port 8000 \
  --gpu-memory-utilization 0.8
```

### 3. API 使用示例

```python
import requests

url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "qwen3",
    "messages": [
        {"role": "system", "content": "你是名医堂的客服助理"},
        {"role": "user", "content": "我想预约按摩"}
    ],
    "temperature": 0.3,
    "max_tokens": 256
}

response = requests.post(url, json=payload)
print(response.json()["choices"][0]["message"]["content"])
```

## 📁 文件结构

```
fine-tune/
├── local_train_8b.py          # 标准训练脚本
├── local_train_8b_save.py     # 显存优化安全训练版本
├── local_train_8b_safe.py     # 版本（解决评估错误）
├── model_test.py              # 自动化测试脚本
├── models_config.json         # 模型配置文件
├── data/
│   ├── clean_train.json       # 训练数据
│   └── chatML.txt            # 原始数据
├── qwen3_output/             # 训练输出
│   ├── v0-*/                 # 训练版本目录
│   ├── v1-*/
│   └── ...
└── README.md                 # 本文档
```

## ❓ 常见问题

### Q1: CUDA 内存不足

**解决方案**:
- 降低 `per_device_train_batch_size` 到 1
- 增加 `gradient_accumulation_steps`
- 使用 4bit 量化 (`quant_bits: 4`)
- 启用 `gradient_checkpointing`

### Q2: 训练速度慢

**解决方案**:
- 减少 `max_length`
- 使用更小的 `lora_rank`
- 启用混合精度训练 (`bf16: true`)

### Q3: 模型回答不符合期望

**解决方案**:
- 检查训练数据质量
- 调整 `learning_rate`
- 增加训练数据量
- 修改系统提示词

### Q4: 推理服务启动失败

**解决方案**:
- 检查模型路径是否正确
- 确认端口未被占用
- 验证模型文件完整性

### Q5: 评估阶段IndexError错误

**错误现象**:
```
IndexError: list assignment index out of range
encoded['labels'][0] = -100
```

**根本原因**:
- 评估阶段某些数据样本编码失败，导致labels列表为空
- chatML格式数据与qwen3模板可能存在兼容性问题
- 训练和评估的数据预处理不一致

**解决方案**:
1. **使用安全训练脚本**:
   ```bash
   python local_train_8b_safe.py
   ```

2. **禁用评估**:
   ```bash
   --eval_strategy no
   ```

3. **切换数据格式**:
   ```bash
   # 从chatML.txt切换到clean_train.json
   --dataset ./data/clean_train.json
   ```

4. **减少评估频率**:
   ```bash
   --eval_steps 1000  # 大幅增加评估间隔
   --save_steps 100   # 保持保存频率
   ```

5. **添加安全参数**:
   ```bash
   --prediction_loss_only true      # 只计算损失
   --dataloader_num_workers 0       # 避免多进程问题
   --ignore_data_skip true          # 忽略数据跳过
   ```

## 📊 性能基准

### 训练性能 (RTX 4060 8GB)

| 配置 | 批次大小 | 显存使用 | 训练时间/epoch |
|------|----------|----------|----------------|
| 4bit量化 | 1 × 16 | ~7.5GB | ~30分钟 |
| 8bit量化 | 1 × 8  | ~6.8GB | ~25分钟 |

### 推理性能

| 配置 | 延迟 | 吞吐量 | 显存占用 |
|------|------|--------|----------|
| 4bit量化 | ~1.2s | ~15 tokens/s | ~4GB |
| FP16 | ~0.8s | ~25 tokens/s | ~16GB |

## 🔗 相关链接

- [ms-swift 官方文档](https://github.com/modelscope/swift)
- [Qwen3 模型介绍](https://github.com/QwenLM/Qwen)
- [LoRA 论文](https://arxiv.org/abs/2106.09685)
- [BitsAndBytes 量化](https://github.com/TimDettmers/bitsandbytes)

## 📝 更新日志

- **v1.0.0**: 初始版本，支持基础训练流程
- **v1.1.0**: 新增 4bit 量化支持
- **v1.2.0**: 添加自动化测试脚本
- **v1.3.0**: 优化显存使用，支持 8GB 显卡
- **v1.4.0**: 解决评估阶段IndexError错误，新增安全训练模式

---

🎯 **快速开始**: `python local_train_8b.py`

📧 **问题反馈**: 如遇到问题，请检查日志文件或提交 Issue。 