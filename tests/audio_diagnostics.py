#!/usr/bin/env python3
"""
音频系统诊断脚本
"""
import asyncio
import os
import json
from pathlib import Path
from tts_client import create_tts_client
from config import FISH_AUDIO_CONFIG

async def run_diagnostics():
    """运行完整的音频系统诊断"""
    print("=" * 60)
    print("🔍 抖音直播弹幕语音客服 - 音频系统诊断")
    print("=" * 60)
    
    # 1. 配置检查
    print("\n📋 1. 配置检查")
    print("-" * 30)
    print(f"Fish Audio API Key: {'✅ 已配置' if FISH_AUDIO_CONFIG['api_key'] else '❌ 未配置'}")
    print(f"Voice ID: {FISH_AUDIO_CONFIG['voice_id']}")
    print(f"音频格式: {FISH_AUDIO_CONFIG['format']}")
    print(f"WebSocket URL: {FISH_AUDIO_CONFIG['websocket_url']}")
    
    # 2. 目录检查
    print("\n📁 2. 目录检查")
    print("-" * 30)
    audio_dir = Path(__file__).parent / "static" / "audio"
    print(f"音频目录: {audio_dir}")
    print(f"目录存在: {'✅' if audio_dir.exists() else '❌'}")
    
    if audio_dir.exists():
        mp3_files = list(audio_dir.glob("*.mp3"))
        opus_files = list(audio_dir.glob("*.opus"))
        print(f"MP3文件数量: {len(mp3_files)}")
        print(f"Opus文件数量: {len(opus_files)}")
    
    # 3. TTS客户端测试
    print("\n🎤 3. TTS客户端测试")
    print("-" * 30)
    
    tts_client = create_tts_client()
    client_type = type(tts_client).__name__
    print(f"TTS客户端类型: {client_type}")
    
    if client_type == "SimpleTTSClient":
        print("❌ 使用简化版TTS客户端（无音频输出）")
        print("   原因: Fish Audio API配置有问题")
        return
    
    # 4. 音频生成测试
    print("\n🎵 4. 音频生成测试")
    print("-" * 30)
    
    test_texts = [
        "你好，欢迎来到我们的餐厅！",
        "感谢您的咨询，我们马上为您安排。",
        "今天推荐我们的特色菜品。"
    ]
    
    success_count = 0
    failed_tests = []
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试 {i}: {text}")
        try:
            audio_path = await tts_client.text_to_speech(text, save_file=True)
            
            if audio_path:
                # 检查文件
                file_path = Path(__file__).parent / "static" / "audio" / audio_path.split("/")[-1]
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    if file_size > 0:
                        print(f"  ✅ 成功 - 文件: {audio_path} ({file_size} bytes)")
                        success_count += 1
                    else:
                        print(f"  ❌ 失败 - 文件为空")
                        failed_tests.append(f"测试{i}: 文件为空")
                else:
                    print(f"  ❌ 失败 - 文件不存在")
                    failed_tests.append(f"测试{i}: 文件不存在")
            else:
                print(f"  ❌ 失败 - 返回None")
                failed_tests.append(f"测试{i}: 返回None")
                
        except Exception as e:
            print(f"  ❌ 异常 - {e}")
            failed_tests.append(f"测试{i}: {e}")
    
    # 5. 生成前端测试数据
    print("\n🌐 5. 前端测试数据生成")
    print("-" * 30)
    
    if success_count > 0:
        # 生成一个测试音频路径供前端测试
        test_audio_path = await tts_client.text_to_speech("前端音频播放测试", save_file=True)
        if test_audio_path:
            print(f"✅ 前端测试音频已生成: {test_audio_path}")
            
            # 生成测试JSON数据
            test_data = {
                "type": "ai_reply",
                "text": "前端音频播放测试",
                "audio_path": test_audio_path,
                "timestamp": 1749613000,
                "generation_method": "诊断测试"
            }
            
            with open("frontend_test_data.json", "w", encoding="utf-8") as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            print("✅ 前端测试数据已生成: frontend_test_data.json")
    
    # 6. 总结报告
    print("\n📊 6. 诊断总结")
    print("=" * 30)
    print(f"总测试数量: {len(test_texts)}")
    print(f"成功数量: {success_count}")
    print(f"失败数量: {len(failed_tests)}")
    
    if success_count == len(test_texts):
        print("🎉 所有测试通过！音频系统工作正常。")
    elif success_count > 0:
        print("⚠️ 部分测试通过，音频系统基本可用。")
        print("失败的测试:")
        for failure in failed_tests:
            print(f"  - {failure}")
    else:
        print("❌ 所有测试失败，音频系统有问题。")
        print("失败的测试:")
        for failure in failed_tests:
            print(f"  - {failure}")
    
    # 7. 修复建议
    print("\n🔧 7. 修复建议")
    print("-" * 30)
    
    if client_type == "SimpleTTSClient":
        print("- 检查Fish Audio API配置")
        print("- 确保.env文件中FISH_AUDIO_API_KEY已设置")
        print("- 验证API密钥有效性")
    elif success_count < len(test_texts):
        print("- 检查网络连接")
        print("- 验证Fish Audio API服务状态")
        print("- 检查API配额限制")
    else:
        print("- 音频系统工作正常")
        print("- 如果前端仍无声音，检查浏览器控制台错误")
        print("- 确保浏览器允许音频播放")
    
    print("\n前端调试建议:")
    print("- 打开浏览器开发者工具")
    print("- 查看控制台日志中的音频相关信息")
    print("- 检查Network选项卡中音频文件的加载情况")
    print("- 确保浏览器未静音且允许自动播放")
    
    await tts_client.close()

if __name__ == "__main__":
    asyncio.run(run_diagnostics()) 