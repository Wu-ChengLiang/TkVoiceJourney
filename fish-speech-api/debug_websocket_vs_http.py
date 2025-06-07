#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比HTTP和WebSocket API调用
找出WebSocket 402错误的原因
"""

import asyncio
import websockets
import ormsgpack
import httpx
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
FISH_API_KEY = os.getenv("FISH_API_KEY", "")
FISH_REFERENCE_ID = os.getenv("FISH_REFERENCE_ID", "")
HTTP_BASE_URL = "https://api.fish.audio/v1"
WS_URL = "wss://api.fish.audio/v1/tts/live"

def test_http_api():
    """测试HTTP REST API（已知可工作）"""
    print("🔍 测试HTTP REST API...")
    
    try:
        # 简单的TTS请求
        request_data = {
            "text": "这是HTTP API测试",
            "format": "mp3",
            "reference_id": FISH_REFERENCE_ID,
            "latency": "normal"
        }
        
        with httpx.Client() as client:
            response = client.post(
                f"{HTTP_BASE_URL}/tts",
                content=ormsgpack.packb(request_data),
                headers={
                    "authorization": f"Bearer {FISH_API_KEY}",
                    "content-type": "application/msgpack",
                    "model": "speech-1.5",
                },
                timeout=30.0
            )
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ HTTP API 测试成功")
                print(f"   音频大小: {len(response.content)} 字节")
                return True
            else:
                print(f"❌ HTTP API 失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ HTTP API 测试异常: {e}")
        return False

async def test_websocket_different_approaches():
    """测试WebSocket的不同连接方式"""
    print("\n🔍 测试WebSocket API（多种方式）...")
    
    test_approaches = [
        {
            "name": "方式1: 默认模型，无model header",
            "headers": {"Authorization": f"Bearer {FISH_API_KEY}"},
            "model_in_start": None
        },
        {
            "name": "方式2: model header = speech-1.5",
            "headers": {
                "Authorization": f"Bearer {FISH_API_KEY}",
                "model": "speech-1.5"
            },
            "model_in_start": None
        },
        {
            "name": "方式3: model header = speech-1.6",
            "headers": {
                "Authorization": f"Bearer {FISH_API_KEY}",
                "model": "speech-1.6"
            },
            "model_in_start": None
        },
        {
            "name": "方式4: 不同的格式(opus)",
            "headers": {"Authorization": f"Bearer {FISH_API_KEY}"},
            "model_in_start": None,
            "format": "opus"
        },
        {
            "name": "方式5: 不同的格式(wav)",
            "headers": {"Authorization": f"Bearer {FISH_API_KEY}"},
            "model_in_start": None,
            "format": "wav"
        }
    ]
    
    for approach in test_approaches:
        print(f"\n📋 {approach['name']}")
        try:
            print(f"   连接头: {approach['headers']}")
            
            async with websockets.connect(
                WS_URL,
                additional_headers=approach['headers'],
                ping_interval=30,
                ping_timeout=5
            ) as websocket:
                
                print("✅ WebSocket连接成功!")
                
                # 发送start事件
                start_request = {
                    "text": "",
                    "latency": "normal",
                    "format": approach.get("format", "mp3"),
                    "temperature": 0.7,
                    "top_p": 0.7,
                    "reference_id": FISH_REFERENCE_ID
                }
                
                start_message = {
                    "event": "start",
                    "request": start_request
                }
                
                await websocket.send(ormsgpack.packb(start_message))
                print("✅ start事件发送成功")
                
                # 发送测试文本
                text_message = {
                    "event": "text",
                    "text": "WebSocket测试 "
                }
                await websocket.send(ormsgpack.packb(text_message))
                print("✅ 文本事件发送成功")
                
                # 发送停止信号
                stop_message = {"event": "stop"}
                await websocket.send(ormsgpack.packb(stop_message))
                print("✅ 停止事件发送成功")
                
                # 接收响应
                success = False
                timeout_count = 0
                while timeout_count < 5:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = ormsgpack.unpackb(message)
                        
                        event_type = data.get("event")
                        print(f"📥 收到事件: {event_type}")
                        
                        if event_type == "audio":
                            print("🎵 WebSocket API 成功！")
                            success = True
                            break
                        elif event_type == "finish":
                            print("🏁 会话结束")
                            break
                        elif event_type == "error":
                            print(f"❌ 服务器错误: {data.get('message', '未知')}")
                            break
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        continue
                
                if success:
                    print(f"🎉 {approach['name']} 成功!")
                    return True
                else:
                    print(f"⚠️ {approach['name']} 未收到音频")
                
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"❌ 连接失败: HTTP {e.status_code}")
            if e.status_code == 402:
                print("   这是付费相关错误")
            elif e.status_code == 401:
                print("   认证失败")
            elif e.status_code == 403:
                print("   权限不足")
        except Exception as e:
            print(f"❌ 连接异常: {e}")
    
    return False

async def test_websocket_with_http_headers():
    """尝试使用和HTTP相同的headers"""
    print("\n🔍 测试WebSocket（模拟HTTP headers）...")
    
    try:
        # 尝试添加更多HTTP风格的headers
        headers = {
            "Authorization": f"Bearer {FISH_API_KEY}",
            "Content-Type": "application/msgpack",  # 虽然WS不需要，但试试
            "model": "speech-1.5",
            "User-Agent": "fish-speech-api/1.0"
        }
        
        print(f"   使用headers: {headers}")
        
        async with websockets.connect(
            WS_URL,
            additional_headers=headers,
            ping_interval=30,
            ping_timeout=5
        ) as websocket:
            print("✅ 连接成功，这种方法有效！")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ 仍然失败: HTTP {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False

def check_api_key_details():
    """检查API Key的详细信息"""
    print("\n🔍 分析API Key...")
    
    if not FISH_API_KEY:
        print("❌ API Key未设置")
        return
    
    print(f"   长度: {len(FISH_API_KEY)}")
    print(f"   前缀: {FISH_API_KEY[:10]}...")
    print(f"   后缀: ...{FISH_API_KEY[-10:]}")
    
    # 检查是否包含特殊字符
    if any(char in FISH_API_KEY for char in [' ', '\n', '\r', '\t']):
        print("⚠️ API Key包含空白字符，可能有问题")
    else:
        print("✅ API Key格式看起来正常")

async def main():
    """主测试函数"""
    print("🧪 Fish Audio API 对比测试")
    print("=" * 60)
    
    # 检查配置
    check_api_key_details()
    
    # 测试HTTP API（已知工作）
    http_success = test_http_api()
    
    # 测试WebSocket API（多种方式）
    if http_success:
        print(f"\n💡 HTTP API工作正常，现在测试WebSocket...")
        
        ws_success = await test_websocket_different_approaches()
        
        if not ws_success:
            print(f"\n🔄 尝试其他WebSocket方法...")
            ws_success = await test_websocket_with_http_headers()
        
        if ws_success:
            print(f"\n🎉 找到了工作的WebSocket方法！")
        else:
            print(f"\n❌ 所有WebSocket方法都失败了")
            print(f"\n💡 结论: WebSocket API可能需要不同的权限或订阅计划")
            print(f"   建议:")
            print(f"   1. 联系Fish Audio支持，询问WebSocket API访问权限")
            print(f"   2. 检查账户是否有实时流式TTS权限")
            print(f"   3. 确认是否需要升级订阅计划以使用WebSocket")
    else:
        print(f"\n❌ HTTP API也失败了，请先解决基础配置问题")

if __name__ == "__main__":
    asyncio.run(main()) 