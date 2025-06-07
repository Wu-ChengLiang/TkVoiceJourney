#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试
测试VLLM和Fish Audio的流式集成
"""

import asyncio
import sys
import os
import time

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.vllm_stream import VLLMStreamClient
from core.fish_websocket import FishWebSocketClient
from core.stream_integration import StreamingVoiceChat
from core.audio_player import AudioPlayer


async def test_vllm_connection():
    """测试VLLM连接"""
    print("=== 测试VLLM连接 ===")
    client = VLLMStreamClient()
    
    if client.test_connection():
        print("✅ VLLM连接成功")
        return True
    else:
        print("❌ VLLM连接失败")
        return False


async def test_vllm_stream():
    """测试VLLM流式生成"""
    print("\n=== 测试VLLM流式生成 ===")
    client = VLLMStreamClient()
    
    try:
        text_parts = []
        async for chunk in client.stream_chat("简单介绍一下你们的服务"):
            print(chunk, end='', flush=True)
            text_parts.append(chunk)
        
        full_text = ''.join(text_parts)
        print(f"\n✅ VLLM流式生成成功，总长度: {len(full_text)} 字符")
        return True
    except Exception as e:
        print(f"\n❌ VLLM流式生成失败: {e}")
        return False


async def test_fish_websocket():
    """测试Fish WebSocket"""
    print("\n=== 测试Fish WebSocket ===")
    client = FishWebSocketClient()
    
    try:
        audio_data = await client.simple_tts("这是一个测试音频")
        
        if audio_data:
            print(f"✅ Fish WebSocket TTS成功，音频大小: {len(audio_data)} 字节")
            
            # 保存测试音频
            with open("test_fish_audio.mp3", "wb") as f:
                f.write(audio_data)
            print("💾 测试音频已保存为 test_fish_audio.mp3")
            return True
        else:
            print("❌ Fish WebSocket TTS失败，未获得音频数据")
            return False
            
    except Exception as e:
        print(f"❌ Fish WebSocket TTS失败: {e}")
        return False


async def test_integration():
    """测试完整集成"""
    print("\n=== 测试完整集成 ===")
    chat = StreamingVoiceChat()
    
    try:
        # 测试音频播放器
        audio_player = AudioPlayer()
        
        # 定义音频回调
        def audio_callback(audio_data):
            print(f"🎵 收到音频数据: {len(audio_data)} 字节")
            # 保存音频文件
            with open("test_integration_audio.mp3", "wb") as f:
                f.write(audio_data)
            print("💾 集成测试音频已保存")
            
            # 可选：播放音频（注释掉避免在测试时播放）
            # audio_player.play_audio_async(audio_data)
        
        # 处理语音聊天
        await chat.process_voice_chat("你好，请简单介绍一下", audio_callback)
        
        print("✅ 完整集成测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 完整集成测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行集成测试...\n")
    
    tests = [
        ("VLLM连接", test_vllm_connection),
        ("VLLM流式生成", test_vllm_stream),
        ("Fish WebSocket", test_fish_websocket),
        ("完整集成", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"正在运行: {test_name}")
        print('='*50)
        
        start_time = time.time()
        try:
            result = await test_func()
            end_time = time.time()
            
            results.append((test_name, result, end_time - start_time))
            
            if result:
                print(f"✅ {test_name} 测试通过 ({end_time - start_time:.2f}s)")
            else:
                print(f"❌ {test_name} 测试失败 ({end_time - start_time:.2f}s)")
                
        except Exception as e:
            end_time = time.time()
            results.append((test_name, False, end_time - start_time))
            print(f"❌ {test_name} 测试异常: {e} ({end_time - start_time:.2f}s)")
    
    # 输出测试总结
    print(f"\n{'='*50}")
    print("📊 测试结果总结")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result, duration in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name:<20} ({duration:.2f}s)")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接。")


def main():
    """主函数"""
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行异常: {e}")


if __name__ == "__main__":
    main() 