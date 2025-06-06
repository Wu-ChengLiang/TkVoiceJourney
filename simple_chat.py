#!/usr/bin/env python3
"""
简单对话脚本 - 修复版 
使用正确的模型路径，专为RTX 4060 8GB显存优化
"""

import os
import sys
import torch
import gc
from pathlib import Path
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    BitsAndBytesConfig
)
from peft import PeftModel
import warnings
warnings.filterwarnings("ignore")

def clear_memory():
    """清理显存"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

def find_model_path():
    """查找模型路径"""
    current_dir = Path.cwd()
    
    # 可能的模型路径
    possible_paths = [
        current_dir / "my_models", 
        current_dir / "my_models_backup",
        
        current_dir.parent / "my_models",
        current_dir / "qwen3_models"
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "config.json").exists():
            return path
    
    return None

def setup_model():
    """设置模型 - 使用最激进的显存优化"""
    
    print("🚀 正在加载模型...")
    clear_memory()
    
    # 查找模型路径
    base_model_path = find_model_path()
    if base_model_path is None:
        print("❌ 未找到基础模型，请检查模型文件")
        return None, None
    
    current_dir = Path.cwd()
    # lora_path = current_dir / "qwen3_output" / "v7-20250529-224742" / "checkpoint-33"
    lora_path = current_dir / "qwen3_output" / "v10-20250530-074122" / "checkpoint-33"
    

    print(f"基础模型: {base_model_path}")
    print(f"LoRA模型: {lora_path}")
    
    # 最激进的4bit量化配置
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    try:
        # 加载tokenizer
        print("📝 加载tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            str(base_model_path),
            trust_remote_code=True,
            padding_side="left"
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 加载基础模型
        print("🧠 加载基础模型...")
        model = AutoModelForCausalLM.from_pretrained(
            str(base_model_path),
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        
        # 加载LoRA模型（如果存在）
        if lora_path.exists():
            print("🔧 加载LoRA适配器...")
            model = PeftModel.from_pretrained(model, str(lora_path))
            print("✅ LoRA模型加载成功")
        else:
            print("⚠️  LoRA模型不存在，使用基础模型")
        
        # 设置模型为推理模式
        model.eval()
        
        print("✅ 模型加载完成!")
        return model, tokenizer
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        clear_memory()
        return None, None

def format_conversation_prompt(history, user_input):
    """格式化对话prompt"""
    
    # 使用美团客服的格式
    prompt_parts = []
    
    # 添加系统提示
    prompt_parts.append("""
    1. 你是名医堂的美团专业客服助理，名医堂秉承‘传承中医文化，服务百姓健康’理念，专注提供‘医养结合’的中医理疗服务。名医堂让优质中医走进社区，为顾客解决疼痛、亚健康及脏腑调理问题。
    2. 语气：要专业、简短、温柔 不要用!感叹号 
    3. 不要承诺你知识范畴之外的事情，如果超出了你的回答范围，请回复：稍等一下，我和老师确认一下，稍后回复您
    4. 所有的具体信息都用xx来表示 如电话\姓名\时间\地点
    """)
    
    # 添加对话历史
    for i in range(0, len(history), 2):
        if i + 1 < len(history):
            user_msg = history[i].replace("用户: ", "")
            assistant_msg = history[i + 1].replace("助手: ", "")
            prompt_parts.append(f"user: {user_msg}")
            prompt_parts.append(f"assistant: {assistant_msg}")
    
    # 添加当前用户输入
    prompt_parts.append(f"user: {user_input}")
    prompt_parts.append("assistant: ")
    
    return "\n".join(prompt_parts)

def chat_with_model(model, tokenizer):
    """与模型对话"""
    
    if model is None or tokenizer is None:
        print("❌ 模型未加载")
        return
    
    print("\n🎯 美团客服助手已就绪！")
    print("输入 'quit'/'exit'/'退出' 结束对话")
    print("=" * 50)
    
    conversation_history = []
    
    # 测试问题建议
    test_questions = [
        "在吗？想预约下午XX点",
        "方便停车吗？",
        "XX老师在吗？预约他XX点",
        "你们营业到几点?"
        "1位，有女老师吗？",
    ]

    print("💡 建议测试问题:")
    for i, q in enumerate(test_questions, 1):
        print(f"  {i}. {q}")
    
    while True:
        # 获取用户输入
        user_input = input("\n🏪 user: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("👋 感谢使用美团客服服务，再见!")
            break
        
        if not user_input:
            continue
        
        try:
            # 格式化prompt
            prompt = format_conversation_prompt(conversation_history, user_input)
            
            # 编码输入
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                max_length=1024,  # 适中的输入长度
                truncation=True,
                padding=True
            ).to(model.device)
            
            # 生成回复
            print("🤖 客服正在为您查询...")
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=200,  # 适中的输出长度 ；要关闭思考模式
                    do_sample=True,
                    temperature=0.2,
                    top_p=0.9,
                    top_k=40,
                    repetition_penalty=1.05,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
            
            # 解码回复
            generated_text = tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            ).strip()
            
            

            # 清理回复文本
            response = generated_text.split("assistant:")[0].strip()
            
            #  # 添加后处理：如果回复中包含换行符，则只取第一行内容；或是禁止user内容生成
            # if '\n' in response:
            #     response = response.split('\n')[0].strip()

            if not response:
                response = "稍等，我需要查询一下"

            #在这里可以到用工具

            # 这里可以用短信通知人员
            
            print(f"👩‍💼 客服: {response}")
            
            # 添加到对话历史
            conversation_history.append(f"user: {user_input}")
            conversation_history.append(f"assistant: {response}")
            
            # 保持对话历史在合理长度
            if len(conversation_history) > 8:
                conversation_history = conversation_history[-8:]
            
            # 清理显存
            clear_memory()
            
        except Exception as e:
            print(f"❌ 生成回复时出错: {e}")
            print("🔄 正在清理显存，请重试...")
            clear_memory()
            continue

def main():
    """主函数"""
    print("🍔 美团客服助手 v7")
    print("基于 Qwen3-8B + LoRA 微调模型")
    print("专为RTX 4060 8GB显存优化")
    print("=" * 50)
    
    # 设置环境变量
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
    
    # 检查CUDA
    if not torch.cuda.is_available():
        print("❌ 未检测到CUDA，请检查GPU驱动")
        return
    
    gpu_name = torch.cuda.get_device_name(0)
    print(f"🔥 使用GPU: {gpu_name}")
    
    # 显存检查
    total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"💾 总显存: {total_memory:.1f}GB")
    
    if total_memory < 7:
        print("⚠️  警告: 显存不足8GB，可能影响性能")
    
    # 加载模型
    model, tokenizer = setup_model()
    
    if model is None:
        print("❌ 模型加载失败，程序退出")
        return
    
    # 开始对话
    chat_with_model(model, tokenizer)
    
    # 清理资源
    clear_memory()
    print("🧹 资源已清理")

if __name__ == "__main__":
    main() 