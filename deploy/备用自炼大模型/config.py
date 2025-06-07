 #!/usr/bin/env python3
"""
TkVoiceJourney 配置文件
支持不同模型和LoRA配置的切换
专为RTX 4060 8GB显存优化
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
import torch

@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    base_path: str
    lora_path: Optional[str] = None
    max_memory_gb: float = 7.0
    description: str = ""

@dataclass
class QuantizationConfig:
    """量化配置"""
    name: str
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_use_double_quant: bool = True
    description: str = ""

class TkVoiceConfig:
    """TkVoiceJourney主配置类"""
    
    def __init__(self):
        self.current_dir = Path.cwd()
        self._setup_model_configs()
        self._setup_quantization_configs()
        
        # 默认配置
        self.default_model = "qwen3_v10"
        self.default_quantization = "ultra_aggressive"
        
        # 性能配置
        self.max_input_length = 1024
        self.max_output_tokens = 200
        self.temperature = 0.2
        self.top_p = 0.9
        self.top_k = 40
        self.repetition_penalty = 1.05
        
        # TTS配置
        self.enable_tts = False
        self.tts_engine = "fish_speech"
        
    def _setup_model_configs(self):
        """设置模型配置"""
        self.model_configs = {
            "qwen3_v7": ModelConfig(
                name="Qwen3 v7",
                base_path=str(self._find_base_model_path()),
                lora_path=str(self.current_dir.parent / "qwen3_output" / "v7-20250529-224742" / "checkpoint-33"),
                max_memory_gb=7.0,
                description="Qwen3-8B 基础模型 + v7 LoRA微调"
            ),
            "qwen3_v10": ModelConfig(
                name="Qwen3 v10",
                base_path=str(self._find_base_model_path()),
                lora_path=str(self.current_dir.parent / "qwen3_output" / "v10-20250530-074122" / "checkpoint-33"),
                max_memory_gb=7.0,
                description="Qwen3-8B 基础模型 + v10 LoRA微调"
            ),
            "qwen3_base": ModelConfig(
                name="Qwen3 Base",
                base_path=str(self._find_base_model_path()),
                lora_path=None,
                max_memory_gb=6.5,
                description="Qwen3-8B 基础模型（无LoRA）"
            )
        }
    
    def _setup_quantization_configs(self):
        """设置量化配置"""
        self.quantization_configs = {
            "ultra_aggressive": QuantizationConfig(
                name="Ultra Aggressive 4-bit",
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype="float16",
                bnb_4bit_use_double_quant=True,
                description="最激进4bit量化，最大化显存节省"
            ),
            "balanced_4bit": QuantizationConfig(
                name="Balanced 4-bit",
                load_in_4bit=True,
                bnb_4bit_quant_type="fp4",
                bnb_4bit_compute_dtype="float16",
                bnb_4bit_use_double_quant=False,
                description="平衡的4bit量化，兼顾性能和显存"
            ),
            "conservative_8bit": QuantizationConfig(
                name="Conservative 8-bit",
                load_in_4bit=False,
                load_in_8bit=True,
                bnb_4bit_compute_dtype="float16",
                description="保守的8bit量化，优先保证精度"
            ),
            "extreme_memory": QuantizationConfig(
                name="Extreme Memory Save",
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype="bfloat16",  # 使用bfloat16进一步节省
                bnb_4bit_use_double_quant=True,
                description="极限显存节省模式（可能影响精度）"
            )
        }
    
    def _find_base_model_path(self) -> Path:
        """查找基础模型路径"""
        possible_paths = [
            self.current_dir / "my_models", 
            self.current_dir / "my_models_backup",
            self.current_dir.parent / "my_models",
            self.current_dir / "qwen3_models"
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "config.json").exists():
                return path
                
        # 如果找不到，返回默认路径
        return self.current_dir / "my_models"
    
    def get_model_config(self, model_name: str = None) -> ModelConfig:
        """获取模型配置"""
        if model_name is None:
            model_name = self.default_model
        return self.model_configs.get(model_name, self.model_configs[self.default_model])
    
    def get_quantization_config(self, quant_name: str = None) -> QuantizationConfig:
        """获取量化配置"""
        if quant_name is None:
            quant_name = self.default_quantization
        return self.quantization_configs.get(quant_name, self.quantization_configs[self.default_quantization])
    
    def get_torch_dtype(self, compute_dtype: str) -> torch.dtype:
        """获取torch数据类型"""
        dtype_mapping = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32
        }
        return dtype_mapping.get(compute_dtype, torch.float16)
    
    def list_available_models(self) -> Dict[str, str]:
        """列出可用模型"""
        return {name: config.description for name, config in self.model_configs.items()}
    
    def list_available_quantizations(self) -> Dict[str, str]:
        """列出可用量化方式"""
        return {name: config.description for name, config in self.quantization_configs.items()}
    
    def validate_gpu_memory(self, required_gb: float = None) -> bool:
        """验证GPU显存是否足够"""
        if not torch.cuda.is_available():
            return False
            
        if required_gb is None:
            required_gb = self.get_model_config().max_memory_gb
            
        total_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        return total_memory_gb >= required_gb
    
    def get_memory_config(self) -> Dict[str, Any]:
        """获取内存优化配置"""
        return {
            "low_cpu_mem_usage": True,
            "device_map": "auto",
            # max_split_size_mb 应该通过环境变量设置，不能传递给模型
        }
    
    def get_generation_config(self) -> Dict[str, Any]:
        """获取生成配置"""
        return {
            "max_new_tokens": self.max_output_tokens,
            "do_sample": True,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "use_cache": True,  # 启用KV缓存
        }

# 延迟创建全局配置实例
def get_config():
    """获取配置实例"""
    if not hasattr(get_config, '_instance'):
        get_config._instance = TkVoiceConfig()
    return get_config._instance

# 向后兼容
config = None

def print_config_info():
    """打印配置信息"""
    cfg = get_config()
    print("🔧 TkVoiceJourney 配置信息")
    print("=" * 50)
    
    print("\n📦 可用模型:")
    for name, desc in cfg.list_available_models().items():
        marker = "✅" if name == cfg.default_model else "  "
        print(f"  {marker} {name}: {desc}")
    
    print("\n⚡ 量化方式:")
    for name, desc in cfg.list_available_quantizations().items():
        marker = "✅" if name == cfg.default_quantization else "  "
        print(f"  {marker} {name}: {desc}")
    
    # GPU信息
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"\n🔥 GPU: {gpu_name}")
        print(f"💾 总显存: {total_memory:.1f}GB")
        
        model_config = cfg.get_model_config()
        if cfg.validate_gpu_memory(model_config.max_memory_gb):
            print(f"✅ 显存足够 (需要 {model_config.max_memory_gb}GB)")
        else:
            print(f"⚠️  显存可能不足 (需要 {model_config.max_memory_gb}GB)")
    else:
        print("\n❌ 未检测到CUDA")

if __name__ == "__main__":
    print_config_info()