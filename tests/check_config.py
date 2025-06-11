#!/usr/bin/env python3
import os
from config import FISH_AUDIO_CONFIG

print("=== Fish Audio TTS 配置检查 ===")
print(f"API Key: {FISH_AUDIO_CONFIG['api_key'][:20]}..." if FISH_AUDIO_CONFIG['api_key'] else "API Key: None")
print(f"Voice ID: {FISH_AUDIO_CONFIG['voice_id']}")
print(f"WebSocket URL: {FISH_AUDIO_CONFIG['websocket_url']}")
print(f"Format: {FISH_AUDIO_CONFIG['format']}")

print("\n=== 环境变量检查 ===")
print(f"FISH_AUDIO_API_KEY: {os.getenv('FISH_AUDIO_API_KEY', 'Not set')}")

print("\n=== 音频目录检查 ===")
from pathlib import Path
audio_dir = Path(__file__).parent / "static" / "audio"
print(f"音频目录: {audio_dir}")
print(f"目录存在: {audio_dir.exists()}")
if audio_dir.exists():
    files = list(audio_dir.glob("*.opus")) + list(audio_dir.glob("*.mp3"))
    print(f"音频文件数量: {len(files)}")
    if files:
        print("最近的文件:", files[-3:]) 