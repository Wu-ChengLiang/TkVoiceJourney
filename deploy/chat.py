 #!/usr/bin/env python3
"""
TkVoiceJourney 优化对话脚本
使用配置系统，支持模型切换和增强量化
包含思维链过滤功能
"""

import os
import sys
import torch
import gc
import re
from pathlib import Path
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    BitsAndBytesConfig
)
from peft import PeftModel
import warnings
warnings.filterwarnings("ignore")

# 导入配置
sys.path.append(str(Path(__file__).parent))
from config import get_config

class OptimizedChatModel:
    """优化的对话模型类"""
    
    def __init__(self, model_name: str = None, quantization: str = None):
        self.config = get_config()
        self.model_name = model_name or self.config.default_model
        self.quantization = quantization or self.config.default_quantization
        self.model = None
        self.tokenizer = None
        self.conversation_history = []
        
    def clear_memory(self):
        """清理显存"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def setup_model(self):
        """设置模型"""
        print("🚀 正在加载优化模型...")
        self.clear_memory()
        
        # 获取配置
        model_config = self.config.get_model_config(self.model_name)
        quant_config = self.config.get_quantization_config(self.quantization)
        
        print(f"📦 模型: {model_config.name}")
        print(f"⚡ 量化: {quant_config.name}")
        print(f"📁 基础模型路径: {model_config.base_path}")
        
        # 验证显存
        if not self.config.validate_gpu_memory(model_config.max_memory_gb):
            print(f"⚠️  警告: 显存可能不足，需要 {model_config.max_memory_gb}GB")
        
        # 设置量化配置
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=quant_config.load_in_4bit,
            load_in_8bit=quant_config.load_in_8bit,
            bnb_4bit_quant_type=quant_config.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=self.config.get_torch_dtype(quant_config.bnb_4bit_compute_dtype),
            bnb_4bit_use_double_quant=quant_config.bnb_4bit_use_double_quant,
        )
        
        try:
            # 加载tokenizer
            print("📝 加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_config.base_path,
                trust_remote_code=True,
                padding_side="left"
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载基础模型
            print("🧠 加载基础模型...")
            memory_config = self.config.get_memory_config()
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_config.base_path,
                quantization_config=bnb_config,
                torch_dtype=self.config.get_torch_dtype(quant_config.bnb_4bit_compute_dtype),
                trust_remote_code=True,
                **memory_config
            )
            
            # 加载LoRA模型（如果存在）
            if model_config.lora_path and Path(model_config.lora_path).exists():
                print("🔧 加载LoRA适配器...")
                self.model = PeftModel.from_pretrained(self.model, model_config.lora_path)
                print("✅ LoRA模型加载成功")
            else:
                print("⚠️  LoRA模型不存在，使用基础模型")
            
            # 设置模型为推理模式
            self.model.eval()
            
            # 打印显存使用情况
            if torch.cuda.is_available():
                memory_used = torch.cuda.memory_allocated() / (1024**3)
                print(f"💾 当前显存使用: {memory_used:.2f}GB")
            
            print("✅ 模型加载完成!")
            return True
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.clear_memory()
            return False
    
    def filter_thinking_chains(self, text: str) -> str:
        """过滤思维链标记和内容"""
        # 去除 <think>...</think> 标记及其内容
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 去除其他可能的思维标记
        text = re.sub(r'<思考>.*?</思考>', '', text, flags=re.DOTALL)
        text = re.sub(r'\[思考\].*?\[/思考\]', '', text, flags=re.DOTALL)
        text = re.sub(r'\[想法\].*?\[/想法\]', '', text, flags=re.DOTALL)
        
        # 清理多余的空白和换行
        text = re.sub(r'\n\s*\n', '\n', text)  # 去除多余空行
        text = re.sub(r'^\s+|\s+$', '', text)  # 去除首尾空白
        
        return text.strip()
    
    def post_process_response(self, response: str) -> str:
        """后处理响应"""
        # 过滤思维链
        response = self.filter_thinking_chains(response)
        
        # 去除assistant:标记
        response = response.split("assistant:")[0].strip()
        
        # 处理换行问题 - 只保留第一段有意义的回复
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            response = lines[0]
        
        # 如果响应为空或包含不当内容，提供默认回复
        if not response or len(response) < 2:
            response = "稍等，我需要查询一下"
        
        # 确保不包含用户输入的重复
        if 'user:' in response.lower():
            response = "稍等一下，我和老师确认一下，稍后回复您"
        
        return response
    
    def format_conversation_prompt(self, user_input: str) -> str:
        """格式化对话prompt"""
        prompt_parts = []
        
        # 添加系统提示
        prompt_parts.append("""你是名医堂的美团专业客服助理，名医堂秉承'传承中医文化，服务百姓健康'理念，专注提供'医养结合'的中医理疗服务。名医堂让优质中医走进社区，为顾客解决疼痛、亚健康及脏腑调理问题。

要求：
1. 语气要专业、简短、温柔，不要用感叹号
2. 不要承诺你知识范畴之外的事情，如果超出了你的回答范围，请回复：稍等一下，我和老师确认一下，稍后回复您
3. 所有的具体信息都用xx来表示，如电话、姓名、时间、地点
4. 直接回答，不要显示思考过程""")
        
        # 添加对话历史（限制长度）
        for i in range(max(0, len(self.conversation_history) - 6), len(self.conversation_history), 2):
            if i + 1 < len(self.conversation_history):
                user_msg = self.conversation_history[i].replace("user: ", "")
                assistant_msg = self.conversation_history[i + 1].replace("assistant: ", "")
                prompt_parts.append(f"user: {user_msg}")
                prompt_parts.append(f"assistant: {assistant_msg}")
        
        # 添加当前用户输入
        prompt_parts.append(f"user: {user_input}")
        prompt_parts.append("assistant: ")
        
        return "\n".join(prompt_parts)
    
    def generate_response(self, user_input: str) -> str:
        """生成回复"""
        if self.model is None or self.tokenizer is None:
            return "模型未加载，请先初始化模型"
        
        try:
            # 格式化prompt
            prompt = self.format_conversation_prompt(user_input)
            
            # 编码输入
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=self.config.max_input_length,
                truncation=True,
                padding=True
            ).to(self.model.device)
            
            # 生成回复
            generation_config = self.config.get_generation_config()
            generation_config.update({
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            })
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    **generation_config
                )
            
            # 解码回复
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            ).strip()
            
            # 后处理
            response = self.post_process_response(generated_text)
            
            # 添加到对话历史
            self.conversation_history.append(f"user: {user_input}")
            self.conversation_history.append(f"assistant: {response}")
            
            # 保持对话历史在合理长度
            if len(self.conversation_history) > 12:
                self.conversation_history = self.conversation_history[-12:]
            
            # 清理显存
            self.clear_memory()
            
            return response
            
        except Exception as e:
            print(f"❌ 生成回复时出错: {e}")
            self.clear_memory()
            return "系统出现问题，请稍后重试"
    
    def chat_loop(self):
        """对话循环"""
        print("\n🎯 优化版美团客服助手已就绪！")
        print("输入 'quit'/'exit'/'退出' 结束对话")
        print("输入 'config' 查看当前配置")
        print("输入 'memory' 查看显存使用情况")
        print("=" * 50)
        
        # 测试问题建议
        test_questions = [
            "在吗？想预约下午XX点",
            "方便停车吗？",
            "XX老师在吗？预约他XX点",
            "你们营业到几点？",
        ]

        print("💡 建议测试问题:")
        for i, q in enumerate(test_questions, 1):
            print(f"  {i}. {q}")
        
        while True:
            # 获取用户输入
            user_input = input("\n🏪 用户: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 感谢使用美团客服服务，再见!")
                break
            elif user_input.lower() == 'config':
                from config import print_config_info
                print_config_info()
                continue
            elif user_input.lower() == 'memory':
                if torch.cuda.is_available():
                    memory_used = torch.cuda.memory_allocated() / (1024**3)
                    memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    print(f"💾 显存使用: {memory_used:.2f}GB / {memory_total:.1f}GB")
                else:
                    print("❌ 未检测到CUDA")
                continue
            
            if not user_input:
                continue
            
            # 生成回复
            print("🤖 客服正在为您查询...")
            response = self.generate_response(user_input)
            print(f"👩‍💼 客服: {response}")

def main():
    """主函数"""
    print("🍔 TkVoiceJourney 优化版客服助手")
    print("基于配置化 Qwen3-8B + LoRA 微调模型")
    print("专为RTX 4060 8GB显存优化")
    print("=" * 50)
    
    # 设置环境变量
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
    
    # 检查CUDA
    if not torch.cuda.is_available():
        print("❌ 未检测到CUDA，请检查GPU驱动")
        return
    
    # 打印配置信息
    from config import print_config_info
    print_config_info()
    
    # 创建聊天模型
    chat_model = OptimizedChatModel()
    
    # 加载模型
    if not chat_model.setup_model():
        print("❌ 模型加载失败，程序退出")
        return
    
    # 开始对话
    chat_model.chat_loop()
    
    # 清理资源
    chat_model.clear_memory()
    print("🧹 资源已清理")

if __name__ == "__main__":
    main()