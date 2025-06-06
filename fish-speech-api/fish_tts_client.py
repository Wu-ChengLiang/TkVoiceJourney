"""
Fish Audio Text-to-Speech Client
支持SDK和Raw API两种调用方式
"""

import os
import httpx
import ormsgpack
from typing import Literal, Optional, List, Generator
from pydantic import BaseModel, conint
from pathlib import Path

# SDK方式需要安装: pip install fish-audio-sdk
try:
    from fish_audio_sdk import Session, TTSRequest, ReferenceAudio
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: fish-audio-sdk not installed. Only Raw API will be available.")


class ServeReferenceAudio(BaseModel):
    """参考音频模型"""
    audio: bytes
    text: str


class ServeTTSRequest(BaseModel):
    """TTS请求模型"""
    text: str
    chunk_length: int = 200  # 100-300
    format: Literal["wav", "pcm", "mp3"] = "mp3"
    mp3_bitrate: Literal[64, 128, 192] = 128
    references: List[ServeReferenceAudio] = []
    reference_id: Optional[str] = None
    normalize: bool = True
    latency: Literal["normal", "balanced"] = "normal"


class FishTTSClient:
    """Fish Audio TTS客户端"""
    
    def __init__(self, api_key: str = "c519c7c1b9a249069c078110c9ed4af9"):
        self.api_key = api_key
        self.base_url = "https://api.fish.audio/v1"
        self.session = None
        
        # 初始化SDK session（如果可用）
        if SDK_AVAILABLE:
            self.session = Session(api_key)
    
    def tts_with_sdk(
        self, 
        text: str, 
        output_file: str,
        reference_id: Optional[str] = None,
        reference_audio: Optional[tuple] = None,
        model: str = "s1-mini"
    ) -> bool:
        """
        使用SDK进行TTS转换
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径
            reference_id: 参考模型ID（来自playground）
            reference_audio: 参考音频元组 (audio_path, text)
            model: 使用的模型 ("speech-1.5", "speech-1.6", "s1", "s1-mini")
        
        Returns:
            转换是否成功
        """
        if not SDK_AVAILABLE:
            print("SDK not available. Please install: pip install fish-audio-sdk")
            return False
        
        try:
            with open(output_file, "wb") as f:
                if reference_id:
                    # 使用reference_id
                    for chunk in self.session.tts(
                        TTSRequest(reference_id=reference_id, text=text),
                        backend=model
                    ):
                        f.write(chunk)
                elif reference_audio:
                    # 使用参考音频
                    audio_path, audio_text = reference_audio
                    with open(audio_path, "rb") as audio_file:
                        audio_data = audio_file.read()
                    
                    for chunk in self.session.tts(
                        TTSRequest(
                            text=text,
                            references=[ReferenceAudio(audio=audio_data, text=audio_text)]
                        ),
                        backend=model
                    ):
                        f.write(chunk)
                else:
                    # 不使用参考音频
                    for chunk in self.session.tts(
                        TTSRequest(text=text),
                        backend=model
                    ):
                        f.write(chunk)
            
            print(f"✅ TTS完成: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ TTS失败: {e}")
            return False
    
    def tts_with_raw_api(
        self,
        text: str,
        output_file: str,
        reference_audio: Optional[tuple] = None,
        reference_id: Optional[str] = None,
        model: str = "speech-1.5",
        format: str = "mp3",
        mp3_bitrate: int = 128,
        latency: str = "normal"
    ) -> bool:
        """
        使用Raw API进行TTS转换
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径
            reference_audio: 参考音频元组 (audio_path, text)
            reference_id: 参考模型ID
            model: 使用的模型
            format: 音频格式 ("wav", "pcm", "mp3")
            mp3_bitrate: MP3比特率 (64, 128, 192)
            latency: 延迟模式 ("normal", "balanced")
        
        Returns:
            转换是否成功
        """
        try:
            # 准备参考音频
            references = []
            if reference_audio:
                audio_path, audio_text = reference_audio
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                references.append(ServeReferenceAudio(audio=audio_data, text=audio_text))
            
            # 创建请求
            request = ServeTTSRequest(
                text=text,
                format=format,
                mp3_bitrate=mp3_bitrate,
                references=references,
                reference_id=reference_id,
                latency=latency
            )
            
            # 发送请求
            with httpx.Client() as client:
                with client.stream(
                    "POST",
                    f"{self.base_url}/tts",
                    content=ormsgpack.packb(request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
                    headers={
                        "authorization": f"Bearer {self.api_key}",
                        "content-type": "application/msgpack",
                        "model": model,
                    },
                    timeout=None,
                ) as response:
                    response.raise_for_status()
                    
                    with open(output_file, "wb") as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)
            
            print(f"✅ TTS完成: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ TTS失败: {e}")
            return False
    
    def tts(
        self,
        text: str,
        output_file: str,
        use_sdk: bool = True,
        **kwargs
    ) -> bool:
        """
        统一的TTS接口，自动选择最佳方式
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径
            use_sdk: 是否优先使用SDK
            **kwargs: 其他参数
        
        Returns:
            转换是否成功
        """
        if use_sdk and SDK_AVAILABLE:
            return self.tts_with_sdk(text, output_file, **kwargs)
        else:
            return self.tts_with_raw_api(text, output_file, **kwargs)


def main():
    """示例用法"""
    client = FishTTSClient()
    
    # 示例1: 使用SDK（如果可用）
    print("=== 使用SDK方式 ===")
    success = client.tts(
        text="你好世界！这是一个测试。",
        output_file="output_sdk.mp3",
        use_sdk=True,
        model="s1-mini"
    )
    
    # 示例2: 使用Raw API
    print("\n=== 使用Raw API方式 ===")
    success = client.tts(
        text="Hello, world! This is a test.",
        output_file="output_raw.mp3",
        use_sdk=False,
        model="speech-1.5"
    )
    
    # 示例3: 使用参考音频（需要有参考音频文件）
    print("\n=== 使用参考音频 ===")
    # 注意：需要有实际的参考音频文件
    # success = client.tts(
    #     text="这是使用参考音频的测试",
    #     output_file="output_with_ref.mp3",
    #     use_sdk=False,
    #     reference_audio=("lengyue.wav", "床也舒服，床有一种魔力,感觉要长在上面了")
    # )


if __name__ == "__main__":
    main() 