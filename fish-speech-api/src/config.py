#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置管理
从根目录.env文件读取所有配置，确保密钥安全
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# 获取项目根目录路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / '.env'

# 加载环境变量
load_dotenv(dotenv_path=ENV_PATH)

# ==================== LLM配置 ====================
# 当前使用模式：可选择 "openai" 或 "vllm"
LLM_MODE = os.getenv("LLM_MODE", "openai")

# OpenAI 配置
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# VLLM 配置
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")
VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen2.5-7B-Instruct")

# ==================== Fish Audio TTS配置 ====================
FISH_API_KEY = os.getenv("FISH_API_KEY", "")
FISH_WS_URL = os.getenv("FISH_WS_URL", "wss://api.fish.audio/v1/tts/live")
FISH_REFERENCE_ID = os.getenv("FISH_REFERENCE_ID", "")

# TTS 配置
TTS_FORMAT = os.getenv("TTS_FORMAT", "mp3")
TTS_LATENCY = os.getenv("TTS_LATENCY", "normal")
TTS_TEMPERATURE = float(os.getenv("TTS_TEMPERATURE", "0.7"))
TTS_TOP_P = float(os.getenv("TTS_TOP_P", "0.7"))
TTS_BACKEND = os.getenv("TTS_BACKEND", "speech-1.6")

# ==================== 应用配置 ====================
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
TEMP_DIR = os.getenv("TEMP_DIR", "temp")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
AUDIO_PLAYER_ENABLED = os.getenv("AUDIO_PLAYER_ENABLED", "true").lower() == "true"

# 创建必要目录
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


def validate_config():
    """验证配置完整性"""
    errors = []
    
    # 验证LLM配置
    if LLM_MODE == "openai" and not OPENAI_API_KEY:
        errors.append("OpenAI API Key 未配置")
    elif LLM_MODE == "vllm" and not VLLM_BASE_URL:
        errors.append("VLLM Base URL 未配置")
    
    # 验证Fish Audio配置
    if not FISH_API_KEY:
        errors.append("Fish Audio API Key 未配置")
    if not FISH_REFERENCE_ID:
        errors.append("Fish Audio Reference ID 未配置")
    
    if errors:
        print("⚠️ 配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        print(f"请检查 {ENV_PATH} 文件")
        return False
    
    print("✅ 配置验证通过")
    return True


def get_current_llm_config():
    """获取当前LLM配置信息"""
    if LLM_MODE == "openai":
        return {
            "mode": "OpenAI",
            "base_url": OPENAI_BASE_URL,
            "model": OPENAI_MODEL,
            "api_key_set": bool(OPENAI_API_KEY)
        }
    else:
        return {
            "mode": "VLLM", 
            "base_url": VLLM_BASE_URL,
            "model": VLLM_MODEL,
            "api_key_set": bool(VLLM_API_KEY and VLLM_API_KEY != "EMPTY")
        }


def print_config_status():
    """打印配置状态"""
    print("=" * 50)
    print("🔧 TkVoiceJourney 配置状态")
    print("=" * 50)
    
    # LLM配置
    llm_config = get_current_llm_config()
    print(f"📝 LLM模式: {llm_config['mode']}")
    print(f"🌐 Base URL: {llm_config['base_url']}")
    print(f"🤖 模型: {llm_config['model']}")
    print(f"🔑 API Key: {'✅ 已配置' if llm_config['api_key_set'] else '❌ 未配置'}")
    
    # Fish Audio配置
    print(f"\n🎵 Fish Audio TTS")
    print(f"🔑 API Key: {'✅ 已配置' if FISH_API_KEY else '❌ 未配置'}")
    print(f"🎤 音色ID: {'✅ 已配置' if FISH_REFERENCE_ID else '❌ 未配置'}")
    print(f"📊 格式: {TTS_FORMAT}")
    print(f"🎛️ 后端: {TTS_BACKEND}")
    
    # 应用配置
    print(f"\n⚙️ 应用配置")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"🐛 调试模式: {'开启' if DEBUG else '关闭'}")
    print(f"🔊 音频播放: {'开启' if AUDIO_PLAYER_ENABLED else '关闭'}")
    
    print("=" * 50)


if __name__ == "__main__":
    print_config_status()
    validate_config() 