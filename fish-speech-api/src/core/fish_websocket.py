#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fish Audio WebSocket Raw API 客户端
基于官方文档的优化实现: https://docs.fish.audio/text-to-speech/text-to-speech-ws#raw-websocket-api-usage
"""

import asyncio
import websockets
import ormsgpack
import sys
import os
from typing import AsyncGenerator, Optional
import io
import concurrent.futures
import base64

# 添加上级目录到路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    FISH_API_KEY, FISH_WS_URL, FISH_REFERENCE_ID, 
    TTS_FORMAT, TTS_LATENCY, TTS_TEMPERATURE, TTS_TOP_P, TTS_BACKEND,
    DEBUG
)


class FishWebSocketClient:
    """Fish Audio WebSocket 客户端 - 基于官方文档优化"""
    
    def __init__(self, api_key: str = None, reference_id: str = None):
        """
        初始化Fish WebSocket客户端
        
        Args:
            api_key: Fish Audio API Key，如果不提供则从配置读取
            reference_id: 音色参考ID，如果不提供则从配置读取
        """
        self.ws_url = FISH_WS_URL
        self.api_key = api_key or FISH_API_KEY
        self.reference_id = reference_id or FISH_REFERENCE_ID
        
        if not self.api_key:
            raise ValueError("Fish Audio API Key 未配置，请在.env文件中设置 FISH_API_KEY")
        if not self.reference_id:
            raise ValueError("Fish Audio Reference ID 未配置，请在.env文件中设置 FISH_REFERENCE_ID")
        
        if DEBUG:
            print(f"🎵 Fish Audio WebSocket 客户端初始化")
            print(f"🌐 WebSocket URL: {self.ws_url}")
            print(f"🎤 音色ID: {self.reference_id}")
            print(f"🎛️ 后端模型: {TTS_BACKEND}")
        
    async def stream_tts(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        流式文本转语音 - 根据官方文档优化
        
        Args:
            text_stream: 异步文本流生成器
            
        Yields:
            bytes: 音频数据块
        """
        try:
            # 准备连接头 - 根据官方文档
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 添加model header（如果指定）
            if TTS_BACKEND and TTS_BACKEND != "speech-1.5":  # 默认是speech-1.5
                headers["model"] = TTS_BACKEND
            
            if DEBUG:
                print(f"🔗 连接到: {self.ws_url}")
                print(f"🔑 Headers: {headers}")
            
            # 建立WebSocket连接
            async with websockets.connect(
                self.ws_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10
            ) as websocket:
                
                if DEBUG:
                    print("✅ WebSocket 连接建立成功")
                
                # 发送开始事件 - 严格按照官方文档格式
                start_request = {
                    "text": "",  # 初始为空文本
                    "latency": TTS_LATENCY,  # "normal" or "balanced"
                    "format": TTS_FORMAT,    # "opus", "mp3", or "wav"
                    "temperature": TTS_TEMPERATURE,
                    "top_p": TTS_TOP_P,
                    "reference_id": self.reference_id
                }
                
                start_message = {
                    "event": "start",
                    "request": start_request
                }
                
                # 如果启用调试，添加debug标志
                if DEBUG:
                    start_message["debug"] = True
                    print(f"📤 发送开始事件: {start_message}")
                
                await websocket.send(ormsgpack.packb(start_message))
                
                # 音频数据收集
                audio_chunks = []
                session_active = True
                text_sent = False
                
                async def receive_audio():
                    """接收音频数据的协程"""
                    nonlocal session_active
                    while session_active:
                        try:
                            # 设置接收超时
                            message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                            data = ormsgpack.unpackb(message)
                            
                            event_type = data.get("event")
                            
                            if event_type == "audio":
                                audio_data = data.get("audio")
                                if audio_data:
                                    # 处理不同类型的音频数据
                                    if isinstance(audio_data, str):
                                        # 如果是base64编码的字符串
                                        try:
                                            audio_bytes = base64.b64decode(audio_data)
                                        except:
                                            audio_bytes = audio_data.encode() if isinstance(audio_data, str) else audio_data
                                    else:
                                        audio_bytes = audio_data
                                    
                                    if audio_bytes:
                                        audio_chunks.append(audio_bytes)
                                        if DEBUG:
                                            print(f"🎵 收到音频块: {len(audio_bytes)} 字节, 总时长: {data.get('time', 'N/A')}ms")
                                        
                            elif event_type == "finish":
                                reason = data.get("reason", "unknown")
                                if DEBUG:
                                    print(f"🏁 会话结束: {reason}")
                                session_active = False
                                break
                                
                            elif event_type == "log" and DEBUG:
                                log_msg = data.get("message", "")
                                print(f"📝 服务器日志: {log_msg}")
                                
                            elif event_type == "error":
                                error_msg = data.get("message", "未知错误")
                                print(f"❌ 服务器错误: {error_msg}")
                                session_active = False
                                break
                                
                        except asyncio.TimeoutError:
                            if DEBUG:
                                print("⏰ 接收音频超时")
                            break
                        except websockets.exceptions.ConnectionClosed:
                            if DEBUG:
                                print("🔌 WebSocket 连接关闭")
                            break
                        except Exception as e:
                            if DEBUG:
                                print(f"❌ 接收音频错误: {e}")
                            break
                    
                    session_active = False

                # 启动音频接收任务
                receive_task = asyncio.create_task(receive_audio())
                
                try:
                    # 发送流式文本
                    text_buffer = ""
                    
                    async for text_chunk in text_stream:
                        if not session_active:
                            break
                            
                        if text_chunk and text_chunk.strip():
                            text_buffer += text_chunk
                            text_sent = True
                            
                            # 根据官方文档建议的文本缓冲策略
                            should_send = (
                                len(text_buffer) >= 20 or  # 缓冲区大小调整
                                any(punct in text_chunk for punct in ['。', '！', '？', '.', '!', '?', '\n', '，', ','])
                            )
                            
                            if should_send:
                                text_message = {
                                    "event": "text",
                                    "text": text_buffer + " "  # 官方文档建议添加空格
                                }
                                await websocket.send(ormsgpack.packb(text_message))
                                if DEBUG:
                                    print(f"📤 发送文本块: {text_buffer}")
                                text_buffer = ""
                    
                    # 发送剩余文本
                    if text_buffer.strip() and session_active:
                        text_message = {
                            "event": "text",
                            "text": text_buffer + " "
                        }
                        await websocket.send(ormsgpack.packb(text_message))
                        if DEBUG:
                            print(f"📤 发送剩余文本: {text_buffer}")
                    
                    # 如果没有发送任何文本，发送默认测试文本
                    if not text_sent and session_active:
                        test_message = {
                            "event": "text", 
                            "text": "测试连接 "
                        }
                        await websocket.send(ormsgpack.packb(test_message))
                        if DEBUG:
                            print("📤 发送测试文本")
                    
                    # 发送停止事件
                    if session_active:
                        stop_message = {"event": "stop"}
                        await websocket.send(ormsgpack.packb(stop_message))
                        if DEBUG:
                            print("🛑 发送停止信号")
                    
                except Exception as e:
                    if DEBUG:
                        print(f"❌ 发送文本过程出错: {e}")
                    session_active = False
                
                # 等待音频接收完成，增加超时保护
                try:
                    await asyncio.wait_for(receive_task, timeout=30.0)
                except asyncio.TimeoutError:
                    if DEBUG:
                        print("⏰ 等待音频接收超时")
                    receive_task.cancel()
                
                # 返回所有音频数据
                if DEBUG:
                    total_size = sum(len(chunk) for chunk in audio_chunks)
                    print(f"✅ TTS 完成，共收到 {len(audio_chunks)} 个音频块，总大小: {total_size} 字节")
                
                for chunk in audio_chunks:
                    if chunk:  # 确保音频块不为空
                        yield chunk
                        
        except websockets.exceptions.InvalidStatusCode as e:
            error_msg = f"WebSocket连接失败，状态码: {e.status_code}"
            if e.status_code == 401:
                error_msg += " - API Key无效或已过期"
            elif e.status_code == 402:
                error_msg += " - 账户余额不足或需要付费，请充值后重试"
            elif e.status_code == 403:
                error_msg += " - 访问被拒绝，请检查API权限"
            elif e.status_code == 429:
                error_msg += " - 请求频率过高，请稍后重试"
            elif e.status_code == 404:
                error_msg += " - 服务未找到，请检查URL"
            
            if DEBUG:
                print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        except websockets.exceptions.ConnectionClosed as e:
            error_msg = f"WebSocket连接异常关闭: {e.code} - {e.reason}"  
            if DEBUG:
                print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Fish WebSocket TTS失败: {str(e)}"
            if DEBUG:
                print(f"❌ {error_msg}")
            raise Exception(error_msg)

    async def simple_tts(self, text: str) -> bytes:
        """
        简单的文本转语音
        
        Args:
            text: 要转换的文本
            
        Returns:
            bytes: 完整的音频数据
        """
        if not text.strip():
            return b""
        
        # 创建简单的文本流
        async def text_generator():
            yield text.strip()
            
        audio_data = b""
        try:
            async for chunk in self.stream_tts(text_generator()):
                if chunk:
                    audio_data += chunk
        except Exception as e:
            if DEBUG:
                print(f"❌ simple_tts 失败: {e}")
            raise e
            
        return audio_data

    async def openai_compatible_tts(self, 
                                   text: str,
                                   voice: str = None,
                                   response_format: str = "mp3",
                                   speed: float = 1.0) -> bytes:
        """
        OpenAI兼容的TTS接口
        
        Args:
            text: 要转换的文本
            voice: 音色名称（保持兼容性，实际使用配置的reference_id）
            response_format: 响应格式
            speed: 语速（保持兼容性）
            
        Returns:
            bytes: 音频数据
        """
        if DEBUG:
            print(f"🔄 OpenAI兼容TTS调用: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        return await self.simple_tts(text)

    def test_connection(self) -> bool:
        """测试WebSocket连接"""
        async def _test():
            try:
                if DEBUG:
                    print("🔍 测试Fish Audio连接...")
                
                # 测试基础连接
                headers = {"Authorization": f"Bearer {self.api_key}"}
                if TTS_BACKEND and TTS_BACKEND != "speech-1.5":
                    headers["model"] = TTS_BACKEND
                
                # 尝试建立连接
                async with websockets.connect(
                    self.ws_url,
                    additional_headers=headers,
                    ping_interval=30,
                    ping_timeout=5
                ) as websocket:
                    
                    # 发送测试请求
                    start_message = {
                        "event": "start",
                        "request": {
                            "text": "",
                            "latency": TTS_LATENCY,
                            "format": TTS_FORMAT,
                            "temperature": TTS_TEMPERATURE,
                            "top_p": TTS_TOP_P,
                            "reference_id": self.reference_id
                        }
                    }
                    
                    await websocket.send(ormsgpack.packb(start_message))
                    
                    # 发送测试文本
                    test_text = {"event": "text", "text": "测试 "}
                    await websocket.send(ormsgpack.packb(test_text))
                    
                    # 发送停止信号
                    stop_message = {"event": "stop"}
                    await websocket.send(ormsgpack.packb(stop_message))
                    
                    # 等待响应
                    audio_received = False
                    timeout_count = 0
                    
                    while timeout_count < 10:  # 最多等待10次
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            data = ormsgpack.unpackb(message)
                            
                            if data.get("event") == "audio":
                                audio_received = True
                                if DEBUG:
                                    print("✅ 收到测试音频响应")
                                break
                            elif data.get("event") == "finish":
                                if DEBUG:
                                    print("🏁 测试会话结束")
                                break
                            elif data.get("event") == "error":
                                if DEBUG:
                                    print(f"❌ 服务器错误: {data.get('message', '未知错误')}")
                                return False
                                
                        except asyncio.TimeoutError:
                            timeout_count += 1
                            if DEBUG:
                                print(f"⏰ 等待响应超时 ({timeout_count}/10)")
                            continue
                        except Exception as e:
                            if DEBUG:
                                print(f"❌ 接收响应错误: {e}")
                            return False
                    
                    success = audio_received
                    if DEBUG:
                        if success:
                            print("✅ Fish Audio连接测试成功")
                        else:
                            print("❌ Fish Audio连接测试失败，未收到音频数据")
                    
                    return success
                
            except websockets.exceptions.InvalidStatusCode as e:
                if DEBUG:
                    print(f"❌ 连接失败，状态码: {e.status_code}")
                    if e.status_code == 401:
                        print("   原因: API Key无效")
                    elif e.status_code == 402:
                        print("   原因: 账户余额不足，需要充值")
                    elif e.status_code == 403:
                        print("   原因: 访问被拒绝")
                return False
            except Exception as e:
                if DEBUG:
                    print(f"❌ Fish Audio连接测试失败: {e}")
                return False
        
        try:
            # 检查是否已有事件循环在运行
            try:
                loop = asyncio.get_running_loop()
                # 如果已有事件循环，创建一个任务
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _test())
                    return future.result(timeout=30)
            except RuntimeError:
                # 没有运行中的事件循环，可以直接使用asyncio.run
                return asyncio.run(_test())
                
        except Exception as e:
            if DEBUG:
                print(f"❌ 连接测试运行失败: {e}")
            return False


async def main():
    """测试用例"""
    print("🧪 测试 Fish Audio WebSocket 客户端...")
    
    try:
        client = FishWebSocketClient()
        
        # 测试连接
        print("🔍 测试连接...")
        if not client.test_connection():
            print("❌ 连接失败，请检查配置")
            return
        
        print("✅ 连接测试成功")
        
        # 测试简单TTS
        print("\n🎵 测试简单TTS...")
        test_text = "你好，这是 Fish Audio 语音合成测试。欢迎使用TkVoiceJourney！"
        audio_data = await client.simple_tts(test_text)
        
        if audio_data:
            # 保存测试音频
            output_path = "test_fish_audio.mp3"
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print(f"✅ 音频保存成功: {output_path} ({len(audio_data)} 字节)")
        else:
            print("❌ 音频生成失败")
        
        # 测试OpenAI兼容接口
        print("\n🔄 测试OpenAI兼容接口...")
        openai_audio = await client.openai_compatible_tts(
            text="这是OpenAI兼容接口的测试",
            voice="default",
            response_format="mp3"
        )
        
        if openai_audio:
            output_path = "test_openai_compatible.mp3"
            with open(output_path, "wb") as f:
                f.write(openai_audio)
            print(f"✅ OpenAI兼容音频保存: {output_path} ({len(openai_audio)} 字节)")
        
        print("\n🎉 所有测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 