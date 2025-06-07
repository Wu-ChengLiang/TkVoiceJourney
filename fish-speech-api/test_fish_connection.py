#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fish Audio 连接诊断脚本
帮助用户诊断Fish Audio WebSocket连接问题
"""

import asyncio
import websockets
import ormsgpack
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Fish Audio 配置
FISH_API_KEY = os.getenv("FISH_API_KEY", "")
FISH_REFERENCE_ID = os.getenv("FISH_REFERENCE_ID", "")
FISH_WS_URL = os.getenv("FISH_WS_URL", "wss://api.fish.audio/v1/tts/live")

def print_config():
    """打印当前配置"""
    print("=" * 60)
    print("🔧 Fish Audio 配置诊断")
    print("=" * 60)
    print(f"📍 WebSocket URL: {FISH_WS_URL}")
    print(f"🔑 API Key: {'✅ 已配置' if FISH_API_KEY else '❌ 未配置'}")
    if FISH_API_KEY:
        print(f"     格式: {FISH_API_KEY[:8]}...{FISH_API_KEY[-4:] if len(FISH_API_KEY) > 12 else '太短'}")
    print(f"🎤 Reference ID: {'✅ 已配置' if FISH_REFERENCE_ID else '❌ 未配置'}")
    if FISH_REFERENCE_ID:
        print(f"     格式: {FISH_REFERENCE_ID}")
    print("=" * 60)

async def test_basic_connection():
    """测试基础WebSocket连接"""
    print("\n🔗 测试基础WebSocket连接...")
    
    if not FISH_API_KEY:
        print("❌ API Key未配置，无法进行连接测试")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {FISH_API_KEY}"}
        print(f"   请求头: {headers}")
        
        # 尝试连接
        print(f"   连接到: {FISH_WS_URL}")
        async with websockets.connect(
            FISH_WS_URL,
            additional_headers=headers,
            ping_interval=30,
            ping_timeout=5
        ) as websocket:
            print("✅ WebSocket连接建立成功")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ 连接失败，HTTP状态码: {e.status_code}")
        if e.status_code == 401:
            print("   🔍 诊断: API Key无效或已过期")
            print("   💡 解决方案:")
            print("     1. 检查.env文件中的FISH_API_KEY是否正确")
            print("     2. 登录Fish Audio官网验证API Key是否有效")
            print("     3. 检查API Key是否有TTS权限")
        elif e.status_code == 402:
            print("   🔍 诊断: 账户余额不足或需要付费")
            print("   💡 解决方案:")
            print("     1. 🚨 立即登录 https://fish.audio 检查账户余额")
            print("     2. 💰 账户充值以继续使用TTS服务")
            print("     3. 📋 检查当前使用配额和计费详情")
            print("     4. 🔍 确认所选套餐是否包含TTS功能")
        elif e.status_code == 403:
            print("   🔍 诊断: 访问被禁止")
            print("   💡 解决方案:")
            print("     1. 检查账户余额是否充足")
            print("     2. 检查API Key权限设置")
        elif e.status_code == 429:
            print("   🔍 诊断: 请求频率过高")
            print("   💡 解决方案: 稍后重试")
        return False
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   🔍 可能原因:")
        print("     1. 网络连接问题")
        print("     2. 防火墙阻止WebSocket连接")
        print("     3. Fish Audio服务临时不可用")
        return False

async def test_tts_request():
    """测试完整TTS请求"""
    print("\n🎵 测试完整TTS请求...")
    
    if not FISH_API_KEY or not FISH_REFERENCE_ID:
        print("❌ API Key或Reference ID未配置，无法进行TTS测试")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {FISH_API_KEY}"}
        
        async with websockets.connect(
            FISH_WS_URL,
            additional_headers=headers,
            ping_interval=30,
            ping_timeout=10
        ) as websocket:
            
            print("✅ WebSocket连接建立")
            
            # 发送开始请求
            start_message = {
                "event": "start",
                "request": {
                    "text": "",
                    "latency": "normal",
                    "format": "mp3",
                    "temperature": 0.7,
                    "top_p": 0.7,
                    "reference_id": FISH_REFERENCE_ID
                },
                "debug": True
            }
            
            print("📤 发送开始请求...")
            print(f"   Reference ID: {FISH_REFERENCE_ID}")
            await websocket.send(ormsgpack.packb(start_message))
            
            # 发送测试文本
            text_message = {
                "event": "text",
                "text": "这是一个连接诊断测试 "
            }
            print("📤 发送测试文本...")
            await websocket.send(ormsgpack.packb(text_message))
            
            # 发送停止信号
            stop_message = {"event": "stop"}
            print("📤 发送停止信号...")
            await websocket.send(ormsgpack.packb(stop_message))
            
            # 接收响应
            audio_received = False
            error_occurred = False
            timeout_count = 0
            
            print("⏳ 等待服务器响应...")
            
            while timeout_count < 15:  # 最多等待15次
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = ormsgpack.unpackb(message)
                    
                    event_type = data.get("event")
                    print(f"📥 收到事件: {event_type}")
                    
                    if event_type == "audio":
                        audio_data = data.get("audio")
                        if audio_data:
                            audio_size = len(audio_data) if isinstance(audio_data, bytes) else len(str(audio_data))
                            print(f"✅ 收到音频数据: {audio_size} 字节")
                            print(f"   时长: {data.get('time', 'N/A')} ms")
                            audio_received = True
                            # 保存测试音频
                            if isinstance(audio_data, bytes):
                                with open("fish_test.mp3", "wb") as f:
                                    f.write(audio_data)
                                print("💾 音频已保存为 fish_test.mp3")
                        
                    elif event_type == "finish":
                        reason = data.get("reason", "unknown")
                        print(f"🏁 会话结束: {reason}")
                        break
                        
                    elif event_type == "log":
                        log_msg = data.get("message", "")
                        print(f"📝 服务器日志: {log_msg}")
                        
                    elif event_type == "error":
                        error_msg = data.get("message", "未知错误")
                        print(f"❌ 服务器错误: {error_msg}")
                        error_occurred = True
                        
                        # 分析错误类型
                        if "reference_id" in error_msg.lower():
                            print("   🔍 诊断: Reference ID问题")
                            print("   💡 解决方案:")
                            print("     1. 检查Reference ID是否正确")
                            print("     2. 确认该音色模型是否存在")
                            print("     3. 尝试在Fish Audio Playground中测试该音色")
                        elif "quota" in error_msg.lower() or "balance" in error_msg.lower():
                            print("   🔍 诊断: 配额或余额不足")
                            print("   💡 解决方案: 充值账户或检查使用限制")
                        
                        break
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏰ 等待超时 ({timeout_count}/15)")
                    continue
                    
                except Exception as e:
                    print(f"❌ 接收消息错误: {e}")
                    error_occurred = True
                    break
            
            if audio_received and not error_occurred:
                print("🎉 TTS测试成功！")
                return True
            elif error_occurred:
                print("❌ TTS测试失败 - 服务器返回错误")
                return False
            else:
                print("❌ TTS测试失败 - 未收到音频数据")
                return False
                
    except Exception as e:
        print(f"❌ TTS测试失败: {e}")
        return False

async def main():
    """主诊断流程"""
    print("🧪 Fish Audio 连接诊断工具")
    print("=" * 60)
    
    # 打印配置
    print_config()
    
    # 检查基础配置
    if not FISH_API_KEY:
        print("\n❌ 致命错误: FISH_API_KEY 未配置")
        print("请在 .env 文件中设置正确的 Fish Audio API Key")
        return
        
    if not FISH_REFERENCE_ID:
        print("\n❌ 致命错误: FISH_REFERENCE_ID 未配置")
        print("请在 .env 文件中设置正确的 Reference ID")
        return
    
    # 执行测试
    results = []
    
    # 测试1: 基础连接
    basic_ok = await test_basic_connection()
    results.append(("基础连接", basic_ok))
    
    if basic_ok:
        # 测试2: 完整TTS请求
        tts_ok = await test_tts_request()
        results.append(("TTS请求", tts_ok))
    else:
        print("⚠️ 基础连接失败，跳过TTS测试")
        results.append(("TTS请求", False))
    
    # 总结报告
    print("\n" + "=" * 60)
    print("📊 诊断报告")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！Fish Audio 配置正确")
        print("💡 如果应用仍有问题，请检查:")
        print("   1. 应用日志中的详细错误信息")
        print("   2. 网络连接稳定性")
        print("   3. 防火墙设置")
    else:
        print("\n❌ 发现问题，请根据上述诊断信息修复配置")
        print("\n🔧 常见解决方案:")
        print("1. 获取正确的 API Key:")
        print("   - 访问 https://fish.audio")
        print("   - 登录并进入API管理页面")
        print("   - 生成或复制API Key")
        print("2. 获取正确的 Reference ID:")
        print("   - 在Fish Audio Playground中选择或上传音色")
        print("   - 复制模型ID作为Reference ID")
        print("3. 检查账户状态:")
        print("   - 确认账户余额充足")
        print("   - 检查API使用配额")


if __name__ == "__main__":
    asyncio.run(main()) 