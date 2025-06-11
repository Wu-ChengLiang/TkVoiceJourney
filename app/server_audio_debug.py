#!/usr/bin/env python3
"""
服务器音频调试脚本
用于排查服务器环境下的音频问题
"""
import asyncio
import json
import time
from pathlib import Path
from tts_client import create_tts_client
from config import FISH_AUDIO_CONFIG

async def server_audio_debug():
    """服务器音频调试"""
    print("🔍 服务器音频调试开始")
    print("=" * 50)
    
    # 1. 环境检查
    print("\n📋 环境检查")
    print("-" * 30)
    print(f"Fish Audio API Key: {'已配置' if FISH_AUDIO_CONFIG['api_key'] else '未配置'}")
    print(f"WebSocket格式: {FISH_AUDIO_CONFIG['format']}")
    print(f"HTTP格式: {FISH_AUDIO_CONFIG.get('http_format', 'mp3')}")
    
    # 2. 创建TTS客户端
    tts_client = create_tts_client()
    client_type = type(tts_client).__name__
    print(f"TTS客户端类型: {client_type}")
    
    if client_type == "SimpleTTSClient":
        print("❌ 使用简化版TTS，无法生成音频")
        return
    
    # 3. 测试音频生成和文件检查
    print("\n🎵 音频生成测试")
    print("-" * 30)
    
    test_text = "这是服务器音频测试"
    print(f"测试文本: {test_text}")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        audio_path = await tts_client.text_to_speech(test_text, save_file=True)
        generation_time = time.time() - start_time
        
        if audio_path:
            print(f"✅ 音频生成成功: {audio_path}")
            print(f"⏱️ 生成耗时: {generation_time:.2f}秒")
            
            # 检查文件
            file_path = Path(__file__).parent / "static" / "audio" / audio_path.split("/")[-1]
            if file_path.exists():
                file_size = file_path.stat().st_size
                file_format = file_path.suffix
                print(f"📁 文件路径: {file_path}")
                print(f"📏 文件大小: {file_size} bytes")
                print(f"🎼 文件格式: {file_format}")
                
                # 检查文件头部（魔术字节）
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                    print(f"🔍 文件头部: {header.hex()}")
                    
                    # 判断文件类型
                    if header.startswith(b'ID3') or header[4:8] == b'ftyp':
                        print("✅ 文件格式正确（MP3）")
                    elif header.startswith(b'OggS'):
                        print("✅ 文件格式正确（Opus/Ogg）")
                    else:
                        print(f"⚠️ 未知文件格式，头部: {header[:8].hex()}")
                
                # 生成前端测试数据
                test_response = {
                    "type": "ai_reply",
                    "text": test_text,
                    "audio_path": audio_path,
                    "timestamp": time.time(),
                    "generation_method": "服务器调试",
                    "file_size": file_size,
                    "file_format": file_format,
                    "generation_time": generation_time
                }
                
                # 保存测试数据
                with open("server_debug_test.json", "w", encoding="utf-8") as f:
                    json.dump(test_response, f, ensure_ascii=False, indent=2)
                
                print(f"💾 测试数据已保存: server_debug_test.json")
                
                return audio_path
            else:
                print(f"❌ 文件不存在: {file_path}")
                
        else:
            print(f"❌ 音频生成失败")
            print(f"⏱️ 失败耗时: {generation_time:.2f}秒")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    
    await tts_client.close()
    
    # 4. 生成前端调试指令
    print("\n🌐 前端调试指令")
    print("-" * 30)
    print("在浏览器控制台执行以下代码进行调试:")
    print()
    print("// 1. 检查音频上下文状态")
    print("console.log('Audio Context:', audioContext);")
    print("console.log('Audio Permission:', audioPermissionGranted);")
    print()
    print("// 2. 测试音频播放")
    if 'audio_path' in locals():
        print(f"playAudio('{audio_path}');")
    print()
    print("// 3. 检查待播放队列")
    print("console.log('Pending Audio Queue:', pendingAudioQueue);")
    print()
    print("// 4. 手动初始化音频")
    print("initAudioContext().then(() => console.log('Audio context initialized'));")
    print()
    print("// 5. 检查浏览器支持")
    print("console.log('HTMLAudioElement support:', 'HTMLAudioElement' in window);")
    print("console.log('Web Audio API support:', 'AudioContext' in window || 'webkitAudioContext' in window);")

if __name__ == "__main__":
    asyncio.run(server_audio_debug()) 