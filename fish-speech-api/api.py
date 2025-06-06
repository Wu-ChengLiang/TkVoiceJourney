# python -m tools.api_server \
#     --listen 0.0.0.0:8080 \
#     --llama-checkpoint-path "checkpoints/openaudio-s1-mini" \
#     --decoder-checkpoint-path "checkpoints/openaudio-s1-mini/codec.pth" \
#     --decoder-config-name modded_dac_vq

#https://speech.fish.audio/inference/ 

# SDK开发，Option 3: Specifying a specific TTS model using the backend parameter
# with open("output3.mp3", "wb") as f:
#     for chunk in session.tts(
#         TTSRequest(text="床也舒服，床有一种魔力,感觉要长在上面了"),
#         backend="s1-mini"  # Specify the TTS model to use
#     ):
#         f.write(chunk)

# Fish Audio TTS API 调用示例
# 基于官方文档: https://docs.fish.audio/text-to-speech/text-to-speech

# SDK开发方式示例（需要安装 fish-audio-sdk）:
# pip install fish-audio-sdk
# from fish_audio_sdk import Session, TTSRequest
# session = Session("your_api_key")
# with open("output3.mp3", "wb") as f:
#     for chunk in session.tts(
#         TTSRequest(text="床也舒服，床有一种魔力,感觉要长在上面了"),
#         backend="s1-mini"  # 指定TTS模型
#     ):
#         f.write(chunk)

from typing import Annotated, Literal
import httpx
import ormsgpack
from pydantic import BaseModel, conint
import os

# API配置
API_KEY = "c519c7c1b9a249069c078110c9ed4af9"
BASE_URL = "https://api.fish.audio/v1"

class ServeReferenceAudio(BaseModel):
    """参考音频数据结构"""
    audio: bytes
    text: str

class ServeTTSRequest(BaseModel):
    """TTS请求数据结构"""
    text: str
    chunk_length: Annotated[int, conint(ge=100, le=300, strict=True)] = 200
    # 音频格式
    format: Literal["wav", "pcm", "mp3"] = "mp3"
    mp3_bitrate: Literal[64, 128, 192] = 128
    # 用于上下文学习的参考音频
    references: list[ServeReferenceAudio] = []
    # 参考ID (例如从 https://fish.audio/m/7f92f8afb8ec43bf81429cc1c9199cb1/ 
    # 提取 7f92f8afb8ec43bf81429cc1c9199cb1)
    reference_id: str | None = None
    # 标准化文本（中英文），提高数字的稳定性
    normalize: bool = True
    # 平衡模式将延迟降至300ms，但可能降低稳定性
    latency: Literal["normal", "balanced"] = "normal"

def text_to_speech(
    text: str,
    output_file: str = "output.mp3",
    reference_audio_path: str | None = None,
    reference_text: str | None = None,
    reference_id: str | None = None,
    model: str = "speech-1.5",
    format: str = "mp3",
    mp3_bitrate: int = 128,
    latency: str = "normal"
) -> bool:
    """
    将文本转换为语音
    
    Args:
        text: 要转换的文本
        output_file: 输出文件路径
        reference_audio_path: 参考音频文件路径
        reference_text: 参考音频对应的文本
        reference_id: 参考模型ID（来自playground）
        model: TTS模型 ("speech-1.5", "speech-1.6", "s1", "s1-mini")
        format: 音频格式 ("wav", "pcm", "mp3")
        mp3_bitrate: MP3比特率 (64, 128, 192)
        latency: 延迟模式 ("normal", "balanced")
    
    Returns:
        是否成功
    """
    try:
        # 准备参考音频
        references = []
        if reference_audio_path and reference_text:
            if os.path.exists(reference_audio_path):
                with open(reference_audio_path, "rb") as f:
                    audio_data = f.read()
                references.append(ServeReferenceAudio(audio=audio_data, text=reference_text))
                print(f"✅ 已加载参考音频: {reference_audio_path}")
            else:
                print(f"⚠️  参考音频文件不存在: {reference_audio_path}")
        
        # 创建请求
        request = ServeTTSRequest(
            text=text,
            format=format,
            mp3_bitrate=mp3_bitrate,
            references=references,
            reference_id=reference_id,
            latency=latency
        )
        
        print(f"🔧 开始TTS转换...")
        print(f"   文本: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"   模型: {model}")
        print(f"   格式: {format}")
        print(f"   输出: {output_file}")
        
        # 发送请求
        with httpx.Client() as client:
            with client.stream(
                "POST",
                f"{BASE_URL}/tts",
                content=ormsgpack.packb(request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
                headers={
                    "authorization": f"Bearer {API_KEY}",  # 修正为Bearer格式
                    "content-type": "application/msgpack",
                    "model": model,
                },
                timeout=60.0,  # 设置超时时间
            ) as response:
                response.raise_for_status()
                
                with open(output_file, "wb") as f:
                    total_bytes = 0
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                        total_bytes += len(chunk)
                
                print(f"✅ TTS转换成功!")
                print(f"   文件大小: {total_bytes / 1024:.1f} KB")
                print(f"   保存路径: {output_file}")
                return True
                
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP错误: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ TTS转换失败: {e}")
        return False

def main():
    """主函数，演示不同的使用方式"""
    
    print("🎵 Fish Audio TTS API 测试")
    print("=" * 50)
    
    # 测试1: 基本文本转语音
    print("\n📝 测试1: 使用指定模型ID进行文本转语音")
    success = text_to_speech(
        text="亲爱的宝子们！小店新出寿喜锅招牌菜，鲜香入味超下饭！现点单享10元折扣 + 送秘制小吃，戳定位秒抢福利，坐标上海南京路，速来解锁你的味蕾惊喜吧！",
        output_file="test1_basic.mp3",
        reference_id="57eab548c7ed4ddc974c4c153cb015b2",  # 使用指定的模型ID
        model="speech-1.5"
    )
    

    # # 测试2: 英文文本
    # print("\n📝 测试2: 英文文本")
    # success = text_to_speech(
    #     text="Hello, world! Welcome to Fish Audio text-to-speech service.",
    #     output_file="test2_english.mp3",
    #     model="s1-mini"
    # )
    

    # # 测试3: 使用参考音频（如果存在）
    # print("\n📝 测试3: 使用参考音频")
    # if os.path.exists("lengyue.wav"):
    #     success = text_to_speech(
    #         text="这是使用参考音频进行声音克隆的测试。",
    #         output_file="test3_with_reference.mp3",
    #         reference_audio_path="lengyue.wav",
    #         reference_text="床也舒服，床有一种魔力,感觉要长在上面了",
    #         model="speech-1.5"
    #     )
    # else:
    #     print("⚠️  未找到参考音频文件 lengyue.wav，跳过测试3")
    
    # # 测试4: 不同格式
    # print("\n📝 测试4: WAV格式输出")
    # success = text_to_speech(
    #     text="这是WAV格式的测试音频。",
    #     output_file="test4_wav_format.wav",
    #     format="wav",
    #     model="speech-1.6"
    # )
    
    print("\n" + "=" * 50)
    print("🎵 测试完成！")

if __name__ == "__main__":
    main()