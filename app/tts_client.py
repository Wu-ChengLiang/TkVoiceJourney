#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS客户端模块
基于fish-speech-api实现文本转语音功能
"""

import asyncio
import hashlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# 添加fish-speech-api路径
project_root = Path(__file__).parent.parent
fish_api_path = project_root / "fish-speech-api" / "静态api调用"
sys.path.insert(0, str(fish_api_path))

try:
    from fish_tts_client import FishTTSClient
except ImportError:
    FishTTSClient = None

logger = logging.getLogger(__name__)


class TTSClient:
    """TTS语音合成客户端"""
    
    def __init__(self, api_key: str = "c519c7c1b9a249069c078110c9ed4af9"):
        self.api_key = api_key
        self.client = None
        self.output_dir = Path(__file__).parent / "static" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Fish TTS客户端
        if FishTTSClient:
            self.client = FishTTSClient(api_key)
            logger.info("✅ Fish TTS客户端初始化成功")
        else:
            logger.error("❌ Fish TTS客户端导入失败")
    
    async def text_to_speech(
        self, 
        text: str, 
        use_sdk: bool = True,
        model: str = "s1-mini",
        format: str = "mp3"
    ) -> Optional[str]:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            use_sdk: 是否使用SDK
            model: 使用的模型
            format: 音频格式
            
        Returns:
            音频文件的相对路径，失败返回None
        """
        if not self.client or not text.strip():
            return None
        
        try:
            # 生成唯一文件名
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            timestamp = int(time.time())
            filename = f"tts_{timestamp}_{text_hash}.{format}"
            output_path = self.output_dir / filename
            
            logger.info(f"🎵 开始TTS转换: {text[:50]}...")
            
            # 在线程池中执行TTS转换
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._tts_sync,
                text,
                str(output_path),
                use_sdk,
                model,
                format
            )
            
            if success and output_path.exists():
                # 返回相对路径
                relative_path = f"/static/audio/{filename}"
                logger.info(f"✅ TTS转换成功: {relative_path}")
                return relative_path
            else:
                logger.error("❌ TTS转换失败")
                return None
                
        except Exception as e:
            logger.error(f"TTS转换异常: {e}")
            return None
    
    def _tts_sync(
        self, 
        text: str, 
        output_path: str, 
        use_sdk: bool, 
        model: str, 
        format: str
    ) -> bool:
        """同步执行TTS转换"""
        try:
            if use_sdk:
                # 使用SDK方式
                return self.client.tts_with_sdk(
                    text=text,
                    output_file=output_path,
                    model=model
                )
            else:
                # 使用Raw API方式
                return self.client.tts_with_raw_api(
                    text=text,
                    output_file=output_path,
                    model=model,
                    format=format
                )
                
        except Exception as e:
            logger.error(f"同步TTS转换失败: {e}")
            return False
    
    async def text_to_speech_stream(self, text: str) -> Optional[bytes]:
        """
        文本转语音流（用于实时播放）
        
        Args:
            text: 要转换的文本
            
        Returns:
            音频数据字节流，失败返回None
        """
        # 暂时使用文件方式，后续可以优化为流式
        audio_path = await self.text_to_speech(text)
        if audio_path:
            try:
                file_path = self.output_dir / Path(audio_path).name
                with open(file_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"读取音频文件失败: {e}")
        
        return None
    
    def clean_old_files(self, max_age_hours: int = 24):
        """清理旧的音频文件"""
        try:
            current_time = time.time()
            for file_path in self.output_dir.glob("tts_*.mp3"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"清理旧音频文件: {file_path.name}")
        except Exception as e:
            logger.error(f"清理音频文件失败: {e}")


# 简化版TTS客户端（如果Fish TTS不可用）
class SimpleTTSClient:
    """简化版TTS客户端（使用系统TTS或其他方案）"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent / "static" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.warning("⚠️ 使用简化版TTS客户端")
    
    async def text_to_speech(self, text: str, **kwargs) -> Optional[str]:
        """简化版文本转语音"""
        try:
            # 这里可以集成其他TTS方案，如：
            # 1. pyttsx3 (本地TTS)
            # 2. Azure Speech Service
            # 3. Google Text-to-Speech
            # 4. 百度语音合成
            
            logger.info(f"简化TTS: {text}")
            
            # 暂时返回None，表示不支持
            return None
            
        except Exception as e:
            logger.error(f"简化TTS失败: {e}")
            return None


# 根据可用性选择TTS客户端
def create_tts_client(**kwargs) -> TTSClient:
    """创建TTS客户端实例"""
    if FishTTSClient:
        return TTSClient(**kwargs)
    else:
        return SimpleTTSClient()


# 兼容性包装
class TTSClient(TTSClient if FishTTSClient else SimpleTTSClient):
    """TTS客户端（自动选择实现）"""
    pass 