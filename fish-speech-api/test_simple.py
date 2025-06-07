#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试脚本
"""

import sys
import os
import asyncio

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))

try:
    from core.vllm_stream import VLLMStreamClient
    print("✅ VLLM模块导入成功")
except Exception as e:
    print(f"❌ VLLM模块导入失败: {e}")

try:
    from core.fish_websocket import FishWebSocketClient
    print("✅ Fish WebSocket模块导入成功")
except Exception as e:
    print(f"❌ Fish WebSocket模块导入失败: {e}")

try:
    from core.audio_player import AudioPlayer
    print("✅ 音频播放器模块导入成功")
except Exception as e:
    print(f"❌ 音频播放器模块导入失败: {e}")

async def test_vllm():
    """测试VLLM连接"""
    try:
        from core.vllm_stream import VLLMStreamClient
        client = VLLMStreamClient()
        if client.test_connection():
            print("✅ VLLM连接测试成功")
            return True
        else:
            print("❌ VLLM连接失败")
            return False
    except Exception as e:
        print(f"❌ VLLM测试异常: {e}")
        return False

async def test_fish():
    """测试Fish Audio"""
    try:
        from core.fish_websocket import FishWebSocketClient
        client = FishWebSocketClient()
        audio_data = await client.simple_tts("测试")
        if audio_data:
            print(f"✅ Fish Audio测试成功: {len(audio_data)} 字节")
            return True
        else:
            print("❌ Fish Audio测试失败")
            return False
    except Exception as e:
        print(f"❌ Fish Audio测试异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 开始简化测试...\n")
    
    print("1. 测试VLLM连接:")
    await test_vllm()
    
    print("\n2. 测试Fish Audio:")
    await test_fish()
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    asyncio.run(main()) 