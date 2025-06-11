#!/usr/bin/env python3
import asyncio
from pathlib import Path
from tts_client import create_tts_client

async def test_audio_generation():
    """测试音频生成"""
    print("=== 测试 TTS 音频生成 ===")
    
    # 创建TTS客户端
    tts_client = create_tts_client()
    print(f"TTS客户端类型: {type(tts_client).__name__}")
    
    # 测试文本
    test_text = "你好，欢迎来到我们的餐厅"
    
    try:
        # 生成音频
        print(f"生成音频: {test_text}")
        audio_path = await tts_client.text_to_speech(test_text, save_file=True)
        
        if audio_path:
            print(f"✅ 音频生成成功: {audio_path}")
            
            # 检查文件
            full_path = Path(__file__).parent / "static" / "audio" / audio_path.split("/")[-1]
            if full_path.exists():
                file_size = full_path.stat().st_size
                print(f"文件大小: {file_size} bytes")
                print(f"文件格式: {full_path.suffix}")
                
                # 检查文件是否为空
                if file_size > 0:
                    print("✅ 音频文件非空")
                else:
                    print("❌ 音频文件为空")
            else:
                print("❌ 音频文件不存在")
        else:
            print("❌ 音频生成失败，返回None")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audio_generation()) 