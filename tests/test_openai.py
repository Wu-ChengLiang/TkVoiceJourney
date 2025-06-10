#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OpenAI API Token有效性
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_openai_api():
    """测试OpenAI API"""
    try:
        from openai import AsyncOpenAI
        
        # 获取配置
        api_key = os.getenv("AI_API_KEY", "")
        api_base = os.getenv("AI_API_BASE", "https://api.openai.com/v1")
        model_name = os.getenv("AI_MODEL_NAME", "gpt-3.5-turbo")
        
        print(f"🔧 API配置:")
        print(f"   API Key: {api_key[:20]}..." if len(api_key) > 20 else f"   API Key: {api_key}")
        print(f"   API Base: {api_base}")
        print(f"   Model: {model_name}")
        print("=" * 50)
        
        # 创建客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base if api_base != "https://api.openai.com/v1" else None,
            timeout=30.0
        )
        
        # 测试API调用
        print("🧪 测试API调用...")
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Hello, please respond with just 'OK'"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API调用成功！响应: {result}")
        
        await client.aclose()
        return True
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_api())
    if success:
        print("\n🎉 OpenAI API配置正确！")
    else:
        print("\n💡 建议:")
        print("1. 检查API Key是否有效")
        print("2. 检查API Base URL是否正确")
        print("3. 检查网络连接")
        print("4. 如果使用第三方API，确认服务是否正常") 