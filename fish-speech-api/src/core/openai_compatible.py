#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI兼容的API接口
将Fish Audio TTS和LLM功能包装成OpenAI SDK可直接调用的格式
"""

import asyncio
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass
import base64
import time
import json

from .vllm_stream import UnifiedLLMClient
from .fish_websocket import FishWebSocketClient


@dataclass
class ChatCompletionChunk:
    """流式聊天完成响应块"""
    id: str
    object: str = "chat.completion.chunk"
    created: int = None
    model: str = "gpt-3.5-turbo"
    
    def __post_init__(self):
        if self.created is None:
            self.created = int(time.time())


@dataclass
class ChatCompletionResponse:
    """聊天完成响应"""
    id: str
    object: str = "chat.completion"
    created: int = None
    model: str = "gpt-3.5-turbo"
    
    def __post_init__(self):
        if self.created is None:
            self.created = int(time.time())


@dataclass
class AudioResponse:
    """音频生成响应"""
    data: bytes
    format: str = "mp3"


class OpenAICompatibleClient:
    """OpenAI兼容的客户端"""
    
    def __init__(self):
        """初始化OpenAI兼容客户端"""
        self.llm_client = UnifiedLLMClient()
        self.tts_client = FishWebSocketClient()
        
    # ==================== Chat Completions API ====================
    
    async def chat_completions_create(self,
                                    messages: List[Dict[str, str]],
                                    model: str = "gpt-3.5-turbo",
                                    stream: bool = False,
                                    temperature: float = 0.7,
                                    max_tokens: Optional[int] = None,
                                    **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        创建聊天完成（兼容OpenAI chat.completions.create接口）
        
        Args:
            messages: 消息列表
            model: 模型名称（保持兼容性，实际使用配置中的模型）
            stream: 是否流式返回
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Yields:
            Dict: 兼容OpenAI格式的响应
        """
        # 提取系统提示词和用户输入
        system_prompt = None
        user_input = ""
        
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            elif message["role"] == "user":
                user_input = message["content"]
        
        if stream:
            # 流式响应
            chunk_id = f"chatcmpl-{int(time.time())}"
            
            async for content in self.llm_client.stream_chat(user_input, system_prompt):
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": content},
                        "finish_reason": None
                    }]
                }
                yield chunk
            
            # 结束块
            end_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield end_chunk
        else:
            # 非流式响应
            full_response = ""
            async for content in self.llm_client.stream_chat(user_input, system_prompt):
                full_response += content
            
            response = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_response
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_input.split()),
                    "completion_tokens": len(full_response.split()),
                    "total_tokens": len(user_input.split()) + len(full_response.split())
                }
            }
            yield response

    # ==================== Audio API ====================
    
    async def audio_speech_create(self,
                                model: str = "tts-1",
                                input: str = "",
                                voice: str = "alloy",
                                response_format: str = "mp3",
                                speed: float = 1.0,
                                **kwargs) -> bytes:
        """
        文本转语音（兼容OpenAI audio.speech.create接口）
        
        Args:
            model: TTS模型名称（保持兼容性）
            input: 输入文本
            voice: 音色名称（保持兼容性）
            response_format: 响应格式
            speed: 语速（保持兼容性）
            **kwargs: 其他参数
            
        Returns:
            bytes: 音频数据
        """
        return await self.tts_client.openai_compatible_tts(
            text=input,
            voice=voice,
            response_format=response_format,
            speed=speed
        )

    async def audio_transcriptions_create(self,
                                        file,
                                        model: str = "whisper-1",
                                        **kwargs) -> Dict[str, Any]:
        """
        语音转文本（暂未实现，保持接口兼容性）
        
        Args:
            file: 音频文件
            model: ASR模型名称
            **kwargs: 其他参数
            
        Returns:
            Dict: 转录结果
        """
        # TODO: 实现ASR功能
        return {
            "text": "语音转文本功能暂未实现"
        }

    # ==================== 流式对话+TTS集成 ====================
    
    async def stream_chat_with_tts(self,
                                 user_input: str,
                                 system_prompt: str = None,
                                 enable_tts: bool = True) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对话 + 实时TTS
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            enable_tts: 是否启用TTS
            
        Yields:
            Dict: 包含文本和音频的响应
        """
        # 收集所有文本用于TTS
        full_text = ""
        text_chunks = []
        
        # 流式获取文本
        async for text_chunk in self.llm_client.stream_chat(user_input, system_prompt):
            full_text += text_chunk
            text_chunks.append(text_chunk)
            
            # 返回文本块
            yield {
                "type": "text",
                "content": text_chunk,
                "full_text": full_text
            }
        
        # 生成TTS音频
        if enable_tts and full_text.strip():
            try:
                audio_data = await self.tts_client.simple_tts(full_text)
                if audio_data:
                    # 返回音频数据（base64编码）
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    yield {
                        "type": "audio", 
                        "content": audio_b64,
                        "format": "mp3",
                        "text": full_text
                    }
            except Exception as e:
                yield {
                    "type": "error",
                    "content": f"TTS生成失败: {str(e)}"
                }

    # ==================== 测试和工具方法 ====================
    
    def test_connection(self) -> Dict[str, bool]:
        """测试所有组件连接"""
        return {
            "llm": self.llm_client.test_connection(),
            "tts": self.tts_client.test_connection()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        llm_status = self.llm_client.test_connection()
        tts_status = self.tts_client.test_connection()
        
        return {
            "status": "healthy" if (llm_status and tts_status) else "unhealthy",
            "components": {
                "llm": "ok" if llm_status else "error",
                "tts": "ok" if tts_status else "error"
            },
            "timestamp": int(time.time())
        }


# ==================== 便捷包装类 ====================

class OpenAI:
    """OpenAI SDK兼容的包装类"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化OpenAI兼容客户端
        
        Args:
            api_key: API Key（保持兼容性，实际从配置读取）
            base_url: Base URL（保持兼容性）
        """
        self.client = OpenAICompatibleClient()
        self.chat = ChatCompletions(self.client)
        self.audio = Audio(self.client)


class ChatCompletions:
    """聊天完成API"""
    
    def __init__(self, client: OpenAICompatibleClient):
        self.client = client
    
    async def create(self, **kwargs):
        """创建聊天完成"""
        stream = kwargs.get('stream', False)
        
        if stream:
            # 返回异步生成器
            return self.client.chat_completions_create(**kwargs)
        else:
            # 返回单个结果
            async for result in self.client.chat_completions_create(**kwargs):
                return result


class Audio:
    """音频API"""
    
    def __init__(self, client: OpenAICompatibleClient):
        self.client = client
        self.speech = Speech(client)
        self.transcriptions = Transcriptions(client)


class Speech:
    """语音合成API"""
    
    def __init__(self, client: OpenAICompatibleClient):
        self.client = client
    
    async def create(self, **kwargs):
        """创建语音"""
        return await self.client.audio_speech_create(**kwargs)


class Transcriptions:
    """语音转录API"""
    
    def __init__(self, client: OpenAICompatibleClient):
        self.client = client
    
    async def create(self, **kwargs):
        """创建转录"""
        return await self.client.audio_transcriptions_create(**kwargs)


# ==================== 测试用例 ====================

async def test_openai_compatible():
    """测试OpenAI兼容接口"""
    print("🧪 测试OpenAI兼容接口...")
    
    try:
        # 创建客户端
        client = OpenAI()
        
        # 测试连接
        print("🔍 测试连接...")
        compatible_client = OpenAICompatibleClient()
        health = await compatible_client.health_check()
        print(f"健康状态: {health}")
        
        if health['status'] != 'healthy':
            print("❌ 服务不健康，请检查配置")
            return
        
        # 测试聊天完成
        print("\n💬 测试聊天完成...")
        response = await client.chat.create(
            messages=[
                {"role": "system", "content": "你是一个友好的助手"},
                {"role": "user", "content": "你好，介绍一下自己"}
            ],
            stream=False
        )
        print(f"回复: {response['choices'][0]['message']['content']}")
        
        # 测试流式聊天
        print("\n🔄 测试流式聊天...")
        print("助手: ", end="", flush=True)
        stream = await client.chat.create(
            messages=[
                {"role": "user", "content": "用一句话介绍人工智能"}
            ],
            stream=True
        )
        
        async for chunk in stream:
            if chunk['choices'][0]['delta'].get('content'):
                print(chunk['choices'][0]['delta']['content'], end="", flush=True)
        print()
        
        # 测试TTS
        print("\n🎵 测试语音合成...")
        audio_data = await client.audio.speech.create(
            model="tts-1",
            input="这是一个测试音频",
            voice="alloy"
        )
        
        if audio_data:
            with open("test_openai_tts.mp3", "wb") as f:
                f.write(audio_data)
            print(f"✅ TTS音频保存成功: test_openai_tts.mp3 ({len(audio_data)} 字节)")
        
        # 测试集成功能
        print("\n🎭 测试流式对话+TTS集成...")
        integrated_stream = compatible_client.stream_chat_with_tts(
            user_input="简单介绍一下Python编程",
            enable_tts=True
        )
        
        full_audio_data = None
        async for chunk in integrated_stream:
            if chunk['type'] == 'text':
                print(chunk['content'], end="", flush=True)
            elif chunk['type'] == 'audio':
                # 解码音频数据
                full_audio_data = base64.b64decode(chunk['content'])
                print(f"\n🎵 收到集成TTS音频: {len(full_audio_data)} 字节")
        
        if full_audio_data:
            with open("test_integrated_tts.mp3", "wb") as f:
                f.write(full_audio_data)
            print("✅ 集成TTS音频保存成功: test_integrated_tts.mp3")
        
        print("\n🎉 所有测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    await test_openai_compatible()


if __name__ == "__main__":
    asyncio.run(main()) 