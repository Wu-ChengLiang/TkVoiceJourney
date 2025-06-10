#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式集成模块
整合VLLM流式文本生成和Fish Audio流式TTS
"""

import asyncio
import sys
import os
from typing import AsyncGenerator

# 添加上级目录到路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .vllm_stream import VLLMStreamClient
from .fish_websocket import FishWebSocketClient
from .audio_player import play_audio


class StreamingVoiceChat:
    def __init__(self):
        """初始化流式语音聊天"""
        self.vllm_client = VLLMStreamClient()
        self.fish_client = FishWebSocketClient()
        self.is_processing = False
        
    async def process_voice_chat(self, user_input: str, play_audio_callback=None):
        """
        处理语音聊天
        
        Args:
            user_input: 用户输入文本
            play_audio_callback: 音频播放回调函数
        """
        if self.is_processing:
            print("⚠️ 正在处理中，请等待...")
            return
            
        self.is_processing = True
        
        try:
            print(f"🤖 用户输入: {user_input}")
            print("🔄 开始生成回答...")
            
            # 获取VLLM流式文本生成
            text_stream = self.vllm_client.stream_chat(user_input)
            
            # 将文本流传递给Fish Audio进行TTS
            audio_data = b""
            async for audio_chunk in self.fish_client.stream_tts(text_stream):
                if audio_chunk:
                    audio_data += audio_chunk
            
            # 播放音频
            if audio_data:
                print(f"🎵 生成音频完成: {len(audio_data)} 字节")
                if play_audio_callback:
                    play_audio_callback(audio_data)
                else:
                    play_audio(audio_data, async_play=True)
            else:
                print("❌ 音频生成失败")
                
        except Exception as e:
            print(f"❌ 处理语音聊天失败: {e}")
        finally:
            self.is_processing = False

    def test_connection(self) -> bool:
        """测试所有服务连接"""
        print("🔍 测试VLLM连接...")
        vllm_ok = self.vllm_client.test_connection()
        
        if vllm_ok:
            print("✅ VLLM连接正常")
        else:
            print("❌ VLLM连接失败")
            
        return vllm_ok


async def main():
    """测试用例"""
    chat = StreamingVoiceChat()
    
    # 测试连接
    if not chat.test_connection():
        print("连接测试失败，退出")
        return
    
    # 测试语音聊天
    test_inputs = [
        "你好，介绍一下你们店的招牌菜",
        "价格怎么样？",
        "今天有什么优惠活动吗？"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n=== 测试 {i}: {user_input} ===")
        await chat.process_voice_chat(user_input)
        
        # 等待一段时间再进行下一个测试
        await asyncio.sleep(2)
    
    print("\n✅ 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(main()) 