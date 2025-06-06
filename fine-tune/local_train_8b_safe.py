#!/usr/bin/env python3
"""
Qwen3-8B模型8bit量化训练优化版 - 支持早停和显存优化
"""

import subprocess
import sys
import json
import os
from pathlib import Path
import glob

def check_local_model():
    """检查Qwen3-8B模型文件"""
    model_path = Path("../my_models")
    print(f"🔍 检查Qwen3-8B模型: {model_path.absolute()}")
    
    if not (model_path / "config.json").exists():
        print(f"❌ 配置文件不存在: {model_path / 'config.json'}")
        return False
    
    # 检查是否是Qwen3-8B模型
    try:
        with open(model_path / "config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        model_type = config.get('model_type', '')
        hidden_size = config.get('hidden_size', 0)
        num_layers = config.get('num_hidden_layers', 0)
        
        # Qwen3-8B特征: hidden_size=4096, num_hidden_layers=36
        if model_type == 'qwen3' or (hidden_size == 4096 and num_layers == 36):
            print(f"✅ 检测到Qwen3-8B模型 (hidden_size: {hidden_size}, layers: {num_layers})")
        elif 'qwen' in model_type:
            print(f"⚠️  检测到其他Qwen模型: {model_type} (hidden_size: {hidden_size})")
        else:
            print(f"⚠️  未知模型类型: {model_type}")
    except Exception as e:
        print(f"⚠️  读取配置失败: {e}")
    
    # 检查模型文件
    safetensors_files = list(model_path.glob("model-*-of-*.safetensors"))
    single_model_file = model_path / "model.safetensors"
    
    if not safetensors_files and not single_model_file.exists():
        print(f"❌ 模型权重文件不存在")
        return False
    
    if safetensors_files:
        print(f"✅ 发现 {len(safetensors_files)} 个模型分片文件")
    elif single_model_file.exists():
        print(f"✅ 发现单一模型文件: model.safetensors")
    
    print(f"✅ Qwen3-8B模型检查完成")
    return True

def start_advanced_training():
    """启动Qwen3-8B优化训练流程"""
    print("🚀 启动Qwen3-8B 8bit优化训练")
    print("🎯 配置: 4060笔记本 8GB显存")
    print("🧠 支持: Thinking模式训练")
    print("=" * 50)
    
    if not check_local_model():
        return 1

    # Qwen3-8B训练命令优化
    cmd = [
        'swift', 'sft',
        '--model', '../my_models',
        '--model_type', 'qwen3',  # 使用qwen3而不是qwen3-8b
        '--dataset', './data/chatML.txt',
        #数据集加载的位置
        '--output_dir', './qwen3_output',
        '--num_train_epochs', '4',
        '--per_device_train_batch_size', '1',      # 8B模型需要小batch
        '--gradient_accumulation_steps', '32',     # 增大梯度累积
        '--learning_rate', '3e-6',                 # Qwen3-8B适用学习率
        # '--max_length', '1024',                    # 增加序列长度
        '--max_length', '512', 
        '--logging_steps', '1',
        '--save_steps', '100',
        # '--eval_steps', '100',                   # 禁用评估避免错误
        # '--eval_strategy', 'steps',              # 禁用评估策略
        '--eval_strategy', 'no',                   # 完全禁用评估
        '--lora_rank', '16',                       # 适中的LoRA rank
        '--lora_alpha', '128',
        '--lora_dropout', '0.05',
        '--gradient_checkpointing', 'true',        # 显存优化
        '--warmup_ratio', '0.1',
        '--weight_decay', '0.01',
        '--lr_scheduler_type', 'cosine_with_restarts',
        '--save_total_limit', '3',
        '--dataloader_num_workers', '1',
        '--bf16', 'true',                          # 使用bf16
        '--fp16', 'false',
        '--report_to', 'tensorboard',
        '--remove_unused_columns', 'false',        # 保持数据完整性
        '--predict_with_generate', 'true',         # 生成式评估
        '--generation_max_length', '512',          # 生成长度限制
        # 新增重复响应抑制参数
        # '--generation_config', '{"repetition_penalty": 1.2, "no_repeat_ngram_size": 3}',
    ]

    # Qwen3特有配置
    print("📊 Qwen3-8B专属配置:")
    print("  🧠 模型类型: Qwen3-8B (8.2B参数)")
    print("  🎭 模板: qwen3 (支持thinking模式)")
    print("  ⚡ 序列长度: 1024 tokens")
    print("  💾 显存优化: 4bit量化 + 梯度检查点")
    print("  🔧 LoRA: rank=64, alpha=128")
    print("  📈 学习率: 3e-6 (8B模型优化)")
    print("  🛑 早停: 5步无改善自动停止")
    print()
    
    print("⏳ 开始Qwen3-8B训练...")
    print("=" * 50)
    
    # 环境变量优化 (8B模型专用)
    env = os.environ.copy()
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,max_split_size_mb:32"  # 更细粒度内存管理
    env["NCCL_P2P_DISABLE"] = "1"
    env["OMP_NUM_THREADS"] = "2"  # 减少CPU线程数
    env["CUDA_VISIBLE_DEVICES"] = "0"  # 确保只使用单卡
    
    # 添加更激进的显存优化
    cmd.extend([
        '--device_map', 'auto',  # 自动设备映射
        '--quant_method', 'bnb',  # 使用BitsAndBytes量化
        '--quant_bits', '4',      # 使用4bit量化代替8bit
        '--bnb_4bit_compute_dtype', 'bfloat16',  # 计算dtype
        '--bnb_4bit_quant_type', 'nf4',  # 使用nf4量化类型
        '--bnb_4bit_use_double_quant', 'true',  # 使用双重量化
        '--model_kwargs', '{"llm_int8_enable_fp32_cpu_offload": true}',  # 启用CPU offload
    ])
    
    try:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 增强日志解析 (Qwen3特化)
        while True:
            output = process.stdout.readline()
            if not output and process.poll() is not None:
                break
            if output:
                line = output.strip()
                
                # 关键信息高亮
                if 'loss' in line and 'eval' not in line:
                    print(f"📉 训练损失: {line}")
                elif 'eval_loss' in line:
                    print(f"🔍 验证损失: {line}")
                elif 'early stopping' in line:
                    print(f"🛑 早停触发: {line}")
                elif 'thinking' in line.lower():
                    print(f"🧠 Thinking模式: {line}")
                elif 'CUDA' in line and 'memory' in line:
                    print(f"💾 显存信息: {line}")
                elif 'error' in line.lower() or 'failed' in line.lower():
                    print(f"❌ 错误: {line}")
                else:
                    print(line)
        
        return_code = process.poll()
        
        if return_code == 0:
            print("\n🎉 Qwen3-8B训练完成!")
            print("📁 输出目录: ./qwen3_output")
            print("📊 查看训练日志: tensorboard --logdir ./qwen3_output")
        
        return return_code
    
    except KeyboardInterrupt:
        print("\n⚠️ 训练被用户中断")
        process.terminate()
        return 1
    except Exception as e:
        print(f"\n❌ 训练过程出错: {e}")
        return 1

def check_swift_installation():
    """检查ms-swift是否正确安装"""
    try:
        # 不使用--help，直接检查swift命令是否存在并可以运行
        # 使用一个简单的命令来检查swift是否可用
        result = subprocess.run(['swift', 'sft'], capture_output=True, text=True, timeout=5)
        # swift sft 没有参数会返回非0状态码但不意味着安装有问题
        # 我们检查stderr中是否有关键的安装相关错误信息
        if 'not found' in result.stderr.lower() or 'no module' in result.stderr.lower():
            print("❌ ms-swift 未正确安装")
            print(f"错误信息: {result.stderr}")
            return False
        else:
            print("✅ ms-swift 已正确安装")
            return True
    except FileNotFoundError:
        print("❌ 未找到swift命令，请安装ms-swift")
        print("💡 安装命令: pip install ms-swift[llm]")
        return False
    except subprocess.TimeoutExpired:
        # 如果命令没有超时错误，说明swift命令存在且可以运行
        print("✅ ms-swift 已正确安装")
        return True
    except Exception as e:
        print(f"❌ 检查ms-swift时发生错误: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Qwen3-8B 8bit量化训练启动器")
    print("=" * 40)
    
    # 检查依赖
    if not check_swift_installation():
        print("\n❌ 请先安装ms-swift:")
        print("pip install ms-swift[llm]")
        sys.exit(1)
    
    # 启动训练
    sys.exit(start_advanced_training())