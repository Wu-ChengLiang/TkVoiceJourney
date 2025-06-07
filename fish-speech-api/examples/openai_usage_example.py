#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI兼容API使用示例
展示如何像使用OpenAI SDK一样调用Fish Audio TTS和LLM API
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.openai_compatible import OpenAI, OpenAICompatibleClient


async def basic_chat_example():
    """基础聊天示例"""
    print("=" * 50)
    print("📝 基础聊天示例")
    print("=" * 50)
    
    # 创建客户端（和OpenAI SDK用法一样）
    client = OpenAI()
    
    # 非流式聊天
    print("\n💬 非流式聊天:")
    response = await client.chat.create(
        messages=[
            {"role": "system", "content": "你是一个友好的中文助手"},
            {"role": "user", "content": "请介绍一下你自己"}
        ],
        model="gpt-3.5-turbo",  # 实际使用配置中的模型
        temperature=0.7,
        stream=False
    )
    
    print(f"助手: {response['choices'][0]['message']['content']}")


async def stream_chat_example():
    """流式聊天示例"""
    print("\n=" * 50)
    print("🔄 流式聊天示例")
    print("=" * 50)
    
    client = OpenAI()
    
    print("\n🔄 流式聊天:")
    print("助手: ", end="", flush=True)
    
    stream = await client.chat.create(
        messages=[
            {"role": "user", "content": "用100字左右介绍一下人工智能的发展历程"}
        ],
        stream=True
    )
    
    async for chunk in stream:
        if chunk['choices'][0]['delta'].get('content'):
            print(chunk['choices'][0]['delta']['content'], end="", flush=True)
    
    print()  # 换行


async def tts_example():
    """文本转语音示例"""
    print("\n=" * 50)
    print("🎵 文本转语音示例")
    print("=" * 50)
    
    client = OpenAI()
    
    # 测试文本
    test_texts = [
        "你好，这是第一个测试音频。",
        "人工智能正在改变我们的世界，让生活变得更加便捷。",
        "Fish Audio 提供了高质量的语音合成服务。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n🎵 生成音频 {i}: {text}")
        
        # 生成音频（和OpenAI TTS API用法一样）
        audio_data = await client.audio.speech.create(
            model="tts-1",  # 实际使用Fish Audio
            input=text,
            voice="alloy",  # 实际使用配置中的音色
            response_format="mp3"
        )
        
        if audio_data:
            filename = f"example_audio_{i}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_data)
            print(f"✅ 音频已保存: {filename} ({len(audio_data)} 字节)")
        else:
            print("❌ 音频生成失败")


async def integrated_chat_tts_example():
    """集成聊天+TTS示例"""
    print("\n=" * 50)
    print("🎭 集成聊天+TTS示例")
    print("=" * 50)
    
    # 使用底层客户端的集成功能
    client = OpenAICompatibleClient()
    
    questions = [
        "请简单介绍一下Python编程语言",
        "什么是机器学习？",
        "人工智能有哪些应用场景？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n🤔 问题 {i}: {question}")
        print("助手: ", end="", flush=True)
        
        # 流式对话+TTS集成
        stream = client.stream_chat_with_tts(
            user_input=question,
            system_prompt="你是一个专业的技术助手，用简洁明了的语言回答问题。",
            enable_tts=True
        )
        
        audio_data = None
        async for chunk in stream:
            if chunk['type'] == 'text':
                print(chunk['content'], end="", flush=True)
            elif chunk['type'] == 'audio':
                import base64
                audio_data = base64.b64decode(chunk['content'])
                print(f"\n🎵 生成TTS音频: {len(audio_data)} 字节")
        
        # 保存音频
        if audio_data:
            filename = f"integrated_audio_{i}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_data)
            print(f"✅ 音频已保存: {filename}")
        
        print()  # 分隔线


async def health_check_example():
    """健康检查示例"""
    print("\n=" * 50)
    print("🏥 健康检查示例")
    print("=" * 50)
    
    client = OpenAICompatibleClient()
    
    print("🔍 检查服务健康状态...")
    health = await client.health_check()
    
    print(f"📊 健康状态: {health['status']}")
    print(f"📋 组件状态:")
    for component, status in health['components'].items():
        emoji = "✅" if status == "ok" else "❌"
        print(f"  {emoji} {component.upper()}: {status}")
    
    # 测试连接
    connections = client.test_connection()
    print(f"\n🔗 连接测试:")
    for service, status in connections.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {service.upper()}: {'连接正常' if status else '连接失败'}")


async def switch_llm_mode_example():
    """演示LLM模式切换"""
    print("\n=" * 50)
    print("🔄 LLM模式切换演示")
    print("=" * 50)
    
    # 这里演示如何通过环境变量切换模式
    # 实际使用时，修改.env文件中的LLM_MODE即可
    
    from src.config import LLM_MODE, get_current_llm_config
    
    print(f"📝 当前LLM模式: {LLM_MODE}")
    config = get_current_llm_config()
    print(f"📊 当前配置: {config}")
    
    print("\n💡 如何切换LLM模式:")
    print("1. 编辑根目录的 .env 文件")
    print("2. 修改 LLM_MODE=openai 或 LLM_MODE=vllm")
    print("3. 配置相应的API Key和Base URL")
    print("4. 重启应用")
    
    print("\n🔧 OpenAI模式配置:")
    print("   LLM_MODE=openai")
    print("   OPENAI_API_KEY=your_openai_key")
    print("   OPENAI_BASE_URL=https://api.openai.com/v1")
    print("   OPENAI_MODEL=gpt-4o-mini")
    
    print("\n🔧 VLLM模式配置:")
    print("   LLM_MODE=vllm")
    print("   VLLM_BASE_URL=https://your-vllm-endpoint.com/v1")
    print("   VLLM_API_KEY=EMPTY")
    print("   VLLM_MODEL=Qwen2.5-7B-Instruct")


async def environment_setup_guide():
    """环境配置指南"""
    print("\n=" * 50)
    print("⚙️ 环境配置指南")
    print("=" * 50)
    
    print("""
📋 配置步骤:

1. 编辑根目录的 .env 文件
2. 配置必要的API密钥:
   - OPENAI_API_KEY (如果使用OpenAI)
   - FISH_API_KEY (Fish Audio TTS)
   - FISH_REFERENCE_ID (Fish Audio 音色ID)

3. 可选配置:
   - VLLM_BASE_URL (如果使用VLLM)
   - TTS_FORMAT, TTS_BACKEND 等

📝 示例 .env 配置:

# LLM配置
LLM_MODE=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Fish Audio TTS配置
FISH_API_KEY=your-fish-audio-key
FISH_REFERENCE_ID=your-reference-id
TTS_FORMAT=mp3
TTS_BACKEND=speech-1.6

🔧 获取Fish Audio配置:
1. 访问 https://fish.audio
2. 注册账户并获取API Key
3. 在Playground中选择或创建音色，获取Reference ID

🚀 使用方法:
   # 像使用OpenAI SDK一样使用
   from src.core.openai_compatible import OpenAI
   
   client = OpenAI()
   response = await client.chat.create(...)
   audio = await client.audio.speech.create(...)
""")


async def main():
    """主函数"""
    print("🎉 TkVoiceJourney OpenAI兼容API 使用示例")
    print("=" * 70)
    
    try:
        # 健康检查
        await health_check_example()
        
        # 检查服务是否健康
        client = OpenAICompatibleClient()
        health = await client.health_check()
        
        if health['status'] != 'healthy':
            print("\n❌ 服务不健康，请检查配置")
            await environment_setup_guide()
            return
        
        # 运行示例
        await basic_chat_example()
        await stream_chat_example()
        await tts_example()
        await integrated_chat_tts_example()
        await switch_llm_mode_example()
        
        print("\n🎉 所有示例运行完成!")
        print("\n📚 查看生成的音频文件:")
        import glob
        audio_files = glob.glob("*.mp3")
        for file in audio_files:
            print(f"  🎵 {file}")
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        print("\n🔧 请检查配置:")
        await environment_setup_guide()
        
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 