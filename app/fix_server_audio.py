#!/usr/bin/env python3
"""
服务器音频问题修复脚本
"""
import asyncio
import json
from pathlib import Path
from tts_client import create_tts_client
from config import FISH_AUDIO_CONFIG

async def fix_server_audio():
    """修复服务器音频问题"""
    print("🔧 服务器音频问题修复")
    print("=" * 50)
    
    # 1. 强制使用HTTP方案生成mp3
    print("\n📋 1. 强制HTTP方案测试（mp3格式）")
    print("-" * 30)
    
    tts_client = create_tts_client()
    
    # 直接使用HTTP备用客户端
    if hasattr(tts_client, 'http_backup'):
        test_text = "前端兼容性测试"
        print(f"测试文本: {test_text}")
        
        try:
            # 强制使用HTTP备用方案
            audio_path = await tts_client.http_backup.text_to_speech(test_text, save_file=True)
            
            if audio_path:
                print(f"✅ HTTP方案生成成功: {audio_path}")
                
                # 检查文件
                file_path = Path(__file__).parent / "static" / "audio" / audio_path.split("/")[-1]
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    file_format = file_path.suffix
                    print(f"📁 文件路径: {file_path}")
                    print(f"📏 文件大小: {file_size} bytes")
                    print(f"🎼 文件格式: {file_format}")
                    
                    # 检查是否为mp3
                    if file_format.lower() == '.mp3':
                        print("✅ MP3格式正确，浏览器兼容性良好")
                        
                        # 生成前端测试数据
                        test_data = {
                            "type": "ai_reply",
                            "text": test_text,
                            "audio_path": audio_path,
                            "timestamp": 1749620500,
                            "file_format": file_format,
                            "file_size": file_size,
                            "generation_method": "HTTP备用方案"
                        }
                        
                        with open("http_test_data.json", "w", encoding="utf-8") as f:
                            json.dump(test_data, f, ensure_ascii=False, indent=2)
                        
                        print("💾 HTTP测试数据已保存: http_test_data.json")
                        return audio_path
                    else:
                        print(f"❌ 文件格式错误: {file_format}")
                else:
                    print("❌ 文件不存在")
            else:
                print("❌ HTTP方案生成失败")
        except Exception as e:
            print(f"❌ HTTP方案异常: {e}")
    
    # 2. 检测当前实际使用的方案
    print("\n📋 2. 检测实际使用的TTS方案")
    print("-" * 30)
    
    test_text2 = "方案检测测试"
    print(f"测试文本: {test_text2}")
    
    try:
        audio_path = await tts_client.text_to_speech(test_text2, save_file=True)
        if audio_path:
            file_path = Path(__file__).parent / "static" / "audio" / audio_path.split("/")[-1]
            if file_path.exists():
                file_format = file_path.suffix
                if file_format.lower() == '.opus':
                    print("⚠️ 当前使用WebSocket方案（opus格式）")
                    print("   这可能导致浏览器兼容性问题")
                elif file_format.lower() == '.mp3':
                    print("✅ 当前使用HTTP备用方案（mp3格式）")
                    print("   浏览器兼容性良好")
                else:
                    print(f"❓ 未知格式: {file_format}")
    except Exception as e:
        print(f"❌ 方案检测异常: {e}")
    
    await tts_client.close()
    
    # 3. 生成前端调试指令
    print("\n🌐 3. 前端调试指令")
    print("-" * 30)
    print("在浏览器控制台执行以下代码:")
    print()
    print("// 1. 检查音频格式支持")
    print("const audio = document.createElement('audio');")
    print("console.log('MP3支持:', audio.canPlayType('audio/mpeg'));")
    print("console.log('Opus支持:', audio.canPlayType('audio/ogg; codecs=opus'));")
    print("console.log('WAV支持:', audio.canPlayType('audio/wav'));")
    print()
    print("// 2. 测试音频路径访问")
    if 'audio_path' in locals():
        print(f"fetch('{audio_path}').then(r => console.log('音频文件可访问:', r.ok));")
    print()
    print("// 3. 检查音频播放权限")
    print("console.log('Audio Context State:', audioContext?.state);")
    print("console.log('Audio Permission:', audioPermissionGranted);")
    print()
    print("// 4. 手动测试音频播放")
    print("const testAudio = new Audio();")
    if 'audio_path' in locals():
        print(f"testAudio.src = '{audio_path}';")
    print("testAudio.play().then(() => console.log('播放成功')).catch(e => console.error('播放失败:', e));")
    
    # 4. 修复建议
    print("\n🔧 4. 修复建议")
    print("-" * 30)
    print("基于测试结果的修复建议:")
    print()
    print("如果生成opus格式:")
    print("- 修改配置强制使用HTTP备用方案")
    print("- 或者在前端添加opus格式检测和降级处理")
    print()
    print("如果生成mp3格式但仍无声音:")
    print("- 检查浏览器自动播放策略")
    print("- 检查音频文件URL是否可访问")
    print("- 检查前端音频权限初始化")

if __name__ == "__main__":
    asyncio.run(fix_server_audio()) 