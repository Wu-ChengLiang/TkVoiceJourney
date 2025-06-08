#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS客户端模块
基于Fish Audio WebSocket API实现流式文本转语音功能
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import AsyncIterator, Optional, Union

import websockets
import ormsgpack
from config import FISH_AUDIO_CONFIG

logger = logging.getLogger(__name__)


class FishAudioWebSocketTTS:
    """Fish Audio WebSocket TTS客户端"""
    
    def __init__(self):
        self.api_key = FISH_AUDIO_CONFIG["api_key"]
        self.websocket_url = FISH_AUDIO_CONFIG["websocket_url"]
        self.voice_id = FISH_AUDIO_CONFIG["voice_id"]
        self.model = FISH_AUDIO_CONFIG["model"]
        self.output_dir = Path(__file__).parent / "static" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 连接状态
        self.is_connected = False
        self.websocket = None
        
        logger.info("✅ Fish Audio WebSocket TTS客户端初始化成功")
    
    async def connect(self) -> bool:
        """连接到Fish Audio WebSocket"""
        try:
            # 修复WebSocket连接参数
            self.websocket = await websockets.connect(
                self.websocket_url,
                additional_headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "model": self.model
                }
            )
            self.is_connected = True
            logger.info("🔗 Fish Audio WebSocket连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket连接失败: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("🔌 WebSocket连接已断开")
    
    async def text_to_speech_stream(self, text_iterator: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """
        流式文本转语音
        
        Args:
            text_iterator: 异步文本迭代器
            
        Yields:
            音频数据块
        """
        if not await self.connect():
            return
        
        try:
            # 发送初始配置
            start_message = {
                "event": "start",
                "request": {
                    "text": "",
                    "latency": FISH_AUDIO_CONFIG["latency"],
                    "format": FISH_AUDIO_CONFIG["format"],
                    "temperature": FISH_AUDIO_CONFIG["temperature"],
                    "top_p": FISH_AUDIO_CONFIG["top_p"],
                    "prosody": FISH_AUDIO_CONFIG["prosody"],
                    "reference_id": self.voice_id
                },
                "debug": True
            }
            
            await self.websocket.send(ormsgpack.packb(start_message))
            logger.info(f"🎤 开始流式TTS，使用声音ID: {self.voice_id}")
            
            # 启动音频接收生成器
            audio_generator = self._receive_audio()
            
            # 发送文本流
            async for text_chunk in text_iterator:
                if text_chunk.strip():
                    text_message = {
                        "event": "text",
                        "text": text_chunk + " "  # 添加空格确保连贯性
                    }
                    await self.websocket.send(ormsgpack.packb(text_message))
                    logger.debug(f"📝 发送文本: {text_chunk}")
            
            # 发送结束信号
            stop_message = {"event": "stop"}
            await self.websocket.send(ormsgpack.packb(stop_message))
            
            # 接收音频数据
            async for audio_chunk in audio_generator:
                yield audio_chunk
                
        except Exception as e:
            logger.error(f"流式TTS失败: {e}")
        finally:
            await self.disconnect()
    
    async def _receive_audio(self) -> AsyncIterator[bytes]:
        """接收音频数据"""
        try:
            while self.is_connected:
                message = await self.websocket.recv()
                data = ormsgpack.unpackb(message)
                
                if data["event"] == "audio":
                    yield data["audio"]
                    logger.debug(f"🎵 接收音频块: {len(data['audio'])} bytes")
                elif data["event"] == "finish":
                    logger.info(f"✅ TTS完成: {data.get('reason', 'unknown')}")
                    break
                elif data["event"] == "log":
                    logger.debug(f"📋 服务器日志: {data.get('message', '')}")
                    
        except Exception as e:
            logger.error(f"接收音频数据失败: {e}")
    
    async def text_to_speech(self, text: str, save_file: bool = True) -> Optional[Union[str, bytes]]:
        """
        文本转语音（完整文本）
        
        Args:
            text: 要转换的文本
            save_file: 是否保存为文件
            
        Returns:
            如果save_file=True，返回文件路径；否则返回音频数据
        """
        if not text.strip():
            return None
        
        try:
            # 创建文本迭代器
            async def text_iterator():
                # 按句子分割文本
                sentences = self._split_text(text)
                for sentence in sentences:
                    yield sentence
            
            audio_chunks = []
            try:
                async for chunk in self.text_to_speech_stream(text_iterator()):
                    audio_chunks.append(chunk)
            except Exception as e:
                logger.error(f"TTS流处理失败: {e}")
                return None
            
            if not audio_chunks:
                logger.warning("没有接收到音频数据")
                return None
            
            # 合并音频数据
            audio_data = b''.join(audio_chunks)
            
            if save_file:
                # 保存为文件
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                timestamp = int(time.time())
                filename = f"tts_{timestamp}_{text_hash}.{FISH_AUDIO_CONFIG['format']}"
                output_path = self.output_dir / filename
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                relative_path = f"/static/audio/{filename}"
                logger.info(f"✅ TTS保存成功: {relative_path}")
                return relative_path
            else:
                return audio_data
                
        except Exception as e:
            logger.error(f"TTS转换失败: {e}")
            return None
    
    def _split_text(self, text: str, max_length: int = 50) -> list:
        """分割文本为合适的块"""
        # 按标点符号分割
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in "。！？!?.，,；;：:" and len(current) > 10:
                sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        # 如果句子太长，进一步分割
        final_sentences = []
        for sentence in sentences:
            if len(sentence) <= max_length:
                final_sentences.append(sentence)
            else:
                # 按长度分割
                words = sentence.split()
                current_chunk = ""
                for word in words:
                    if len(current_chunk + word) <= max_length:
                        current_chunk += word + " "
                    else:
                        if current_chunk:
                            final_sentences.append(current_chunk.strip())
                        current_chunk = word + " "
                if current_chunk:
                    final_sentences.append(current_chunk.strip())
        
        return final_sentences
    
    def clean_old_files(self, max_age_hours: int = 24):
        """清理旧的音频文件"""
        try:
            current_time = time.time()
            for file_path in self.output_dir.glob("tts_*.*"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"清理旧音频文件: {file_path.name}")
        except Exception as e:
            logger.error(f"清理音频文件失败: {e}")


class StreamingTTSClient:
    """流式TTS客户端（结合AI回复流和TTS流）"""
    
    def __init__(self):
        self.fish_tts = FishAudioWebSocketTTS()
        self.current_session = None
        
    async def text_stream_to_audio_stream(self, text_stream: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """
        将文本流转换为音频流
        
        Args:
            text_stream: 异步文本流（来自AI回复生成器）
            
        Yields:
            音频数据块
        """
        try:
            # 缓冲文本片段，达到一定长度后进行TTS
            text_buffer = ""
            buffer_size = 30  # 缓冲区大小
            
            async def buffered_text_iterator():
                nonlocal text_buffer
                
                async for text_chunk in text_stream:
                    text_buffer += text_chunk
                    
                    # 检查是否有完整的句子
                    sentences = self._extract_complete_sentences(text_buffer)
                    for sentence in sentences:
                        if len(sentence.strip()) > 5:  # 过滤太短的句子
                            yield sentence
                            text_buffer = text_buffer.replace(sentence, "", 1)
                
                # 处理剩余文本
                if text_buffer.strip():
                    yield text_buffer.strip()
            
            # 流式TTS转换
            async for audio_chunk in self.fish_tts.text_to_speech_stream(buffered_text_iterator()):
                yield audio_chunk
                
        except Exception as e:
            logger.error(f"流式TTS转换失败: {e}")
    
    def _extract_complete_sentences(self, text: str) -> list:
        """提取完整的句子"""
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in "。！？!?.，,；;：:" and len(current_sentence) > 10:
                sentences.append(current_sentence)
                current_sentence = ""
        
        return sentences
    
    async def text_to_speech(self, text: str, save_file: bool = True) -> Optional[Union[str, bytes]]:
        """兼容性方法"""
        return await self.fish_tts.text_to_speech(text, save_file)
    
    async def close(self):
        """关闭连接"""
        await self.fish_tts.disconnect()


# 简化版TTS客户端（兜底方案）
class SimpleTTSClient:
    """简化版TTS客户端"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent / "static" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.warning("⚠️ 使用简化版TTS客户端")
    
    async def text_to_speech(self, text: str, save_file: bool = True) -> Optional[Union[str, bytes]]:
        """简化版文本转语音"""
        logger.info(f"简化TTS: {text}")
        return None
    
    async def text_stream_to_audio_stream(self, text_stream: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """简化版流式TTS"""
        async for text_chunk in text_stream:
            logger.info(f"简化TTS块: {text_chunk}")
            # 返回空音频块
            yield b''
    
    async def close(self):
        """关闭连接"""
        pass


# 工厂函数
def create_tts_client() -> Union[StreamingTTSClient, SimpleTTSClient]:
    """创建TTS客户端实例"""
    try:
        # 检查是否有有效的API配置
        if FISH_AUDIO_CONFIG["api_key"] and FISH_AUDIO_CONFIG["voice_id"]:
            return StreamingTTSClient()
        else:
            logger.warning("未配置Fish Audio API，使用简化版TTS")
            return SimpleTTSClient()
    except Exception as e:
        logger.warning(f"创建Fish Audio TTS失败，使用简化版: {e}")
        return SimpleTTSClient()


# 兼容性别名
TTSClient = StreamingTTSClient 