#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TTS系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tts_client import create_tts_client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_tts():
    """测试TTS客户端"""
    print("🔧 初始化TTS客户端...")
    
    tts_client = create_tts_client()
    if not tts_client:
        print("❌ TTS客户端创建失败")
        return
    
    print("✅ TTS客户端创建成功")
    
    # 测试文本
    test_texts = [
        "测试Fish Audio语音合成",
        "亲，稍等哦，小助理马上去通知店家确认~ 🔥✨",
        "早10点到晚10点都营业哦，欢迎随时来~ 🕙"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"文本: {text}")
        
        try:
            # 测试TTS生成
            audio_path = await tts_client.text_to_speech(text)
            if audio_path:
                print(f"✅ 音频生成成功: {audio_path}")
            else:
                print("❌ 音频生成失败")
                
        except Exception as e:
            print(f"❌ TTS测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 清理资源
    if hasattr(tts_client, 'close'):
        await tts_client.close()
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_tts()) 