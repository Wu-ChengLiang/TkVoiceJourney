#!/usr/bin/env python3
"""
使用本地1.5B模型的微调训练脚本 - 4.5阶段优化版本
"""

import subprocess
import sys
import json
from pathlib import Path

def check_local_model():
    """检查本地模型文件"""
    model_path = Path("../my_models")
    model_file = model_path / "model.safetensors"
    
    print(f"🔍 检查本地模型: {model_path.absolute()}")
    
    if not model_path.exists():
        print(f"❌ 模型目录不存在: {model_path}")
        return False
    
    if not model_file.exists():
        print(f"❌ 模型文件不存在: {model_file}")
        return False
    
    # 检查其他必要文件
    required_files = ['config.json', 'tokenizer.json', 'tokenizer_config.json']
    missing_files = []
    
    for file in required_files:
        if not (model_path / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  缺少文件: {missing_files}")
        print("训练可能会遇到问题，但仍会尝试继续...")
    
    print(f"✅ 模型文件检查完成")
    print(f"📁 模型路径: {model_path.absolute()}")
    print(f"📦 模型文件大小: {model_file.stat().st_size / (1024**3):.2f} GB")
    
    return True

def create_local_dataset():
    """创建本地训练数据集"""
    data_path = Path("./data/clean_train.json")
    
    if not data_path.exists():
        print(f"❌ 训练数据不存在: {data_path}")
        return None
    
    print(f"✅ 使用清洁训练数据: {data_path}")
    return data_path

def start_local_training():
    """启动本地模型训练"""
    
    print("🚀 启动4.5阶段：重新训练优化后的模型")
    print("🎯 配置: 4060笔记本 8GB显存")
    print("=" * 50)
    
    # 检查本地模型
    if not check_local_model():
        print("❌ 本地模型检查失败")
        return 1
    
    # 创建训练数据
    data_path = create_local_dataset()
    if not data_path:
        return 1
    
    # 本地模型路径
    model_path = str(Path("../my_models").absolute())
    
    # 训练命令 - 4.5阶段优化配置
    cmd = [
        'swift', 'sft',
        '--model', model_path,  # 使用本地模型
        '--model_type', 'qwen3',  # 假设是qwen3架构
        '--dataset', str(data_path.absolute()),
        '--template', 'chatml',
        '--output_dir', './output',
        '--num_train_epochs', '2',  # 减少到2轮，避免过拟合
        '--per_device_train_batch_size', '1',  # 进一步减少batch size确保稳定
        '--gradient_accumulation_steps', '8',  # 补偿batch_size减少
        '--learning_rate', '1e-5',  # 降低学习率，更温和的学习
        '--max_length', '256',  # 减少到256，避免学习过长序列
        '--logging_steps', '1',
        '--save_steps', '25',  # 更频繁保存，便于早停
        '--eval_steps', '25',  # 更频繁评估
        '--lora_rank', '64',  # 保持较大的LoRA rank
        '--lora_alpha', '128',  # alpha = 2 * rank
        '--lora_dropout', '0.1',
        '--gradient_checkpointing',  # 节省显存
        '--warmup_ratio', '0.05',  # 减少warmup比例
        '--weight_decay', '0.01',
        '--lr_scheduler_type', 'cosine',
        '--save_total_limit', '3',  # 只保留最近3个检查点
        '--dataloader_num_workers', '2',  # 减少worker数量
        '--fp16', 'true',  # 使用FP16节省显存
        '--bf16', 'false',  # 显式禁用bf16
        '--torch_dtype', 'float16',  # 设置torch数据类型
        '--report_to', 'tensorboard'  # 启用tensorboard监控
    ]
    
    print("🔧 训练配置:")
    print(f"  📦 模型: 本地1.5B模型 ({model_path})")
    with open(data_path, 'r', encoding='utf-8') as f:
        data_count = len(json.load(f))
    print(f"  📊 数据: {data_count}条训练样本")
    print(f"  🎯 批次大小: 1 (梯度累积: 8, 有效批次: 8)")
    print(f"  📏 序列长度: 256")
    print(f"  🔄 训练轮数: 2")
    print(f"  📈 学习率: 1e-5")
    print(f"  🔧 LoRA: rank=64, alpha=128")
    print(f"  💾 显存优化: FP16 + 梯度检查点")
    print()
    
    print("⏳ 开始训练...")
    print("=" * 50)
    
    # 启动训练进程
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时显示输出
        step_count = 0
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                print(line)
                
                # 检测训练步数
                if 'train_loss' in line or 'loss' in line:
                    step_count += 1
                    if step_count % 10 == 0:
                        print(f"📊 已完成 {step_count} 步训练")
        
        # 等待进程完成
        return_code = process.wait()
        
        if return_code == 0:
            print("\n🎉 4.5阶段训练成功完成！")
            print("📁 输出目录:", Path("./output").absolute())
            print("📊 TensorBoard日志:", Path("./output").absolute() / "runs")
            print("\n💡 查看训练效果:")
            print("  tensorboard --logdir ./output/runs")
        else:
            print(f"\n❌ 训练失败，返回码: {return_code}")
            
        return return_code
        
    except KeyboardInterrupt:
        print("\n⚠️  训练被用户中断")
        if process:
            process.terminate()
        return 1
    except Exception as e:
        print(f"\n❌ 训练过程出错: {e}")
        return 1

if __name__ == "__main__":
    exit_code = start_local_training()
    sys.exit(exit_code) 