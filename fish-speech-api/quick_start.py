#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TkVoiceJourney 快速启动脚本
帮助用户验证配置并快速体验OpenAI兼容的Fish Audio TTS功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.config import validate_config, print_config_status
    from src.core.openai_compatible import OpenAI, OpenAICompatibleClient
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print("🎉 欢迎使用 TkVoiceJourney")
    print("🎵 OpenAI兼容的Fish Audio TTS系统")
    print("=" * 70)


async def quick_demo():
    """快速演示"""
    print("\n🚀 开始快速演示...")
    
    try:
        # 创建客户端
        client = OpenAI()
        compatible_client = OpenAICompatibleClient()
        
        # 健康检查
        print("\n🏥 健康检查...")
        health = await compatible_client.health_check()
        
        if health['status'] != 'healthy':
            print("❌ 系统不健康，请检查配置后重试")
            return False
        
        print("✅ 系统健康检查通过")
        
        # 简单聊天测试
        print("\n💬 测试聊天功能...")
        try:
            response = await client.chat.create(
                messages=[
                    {"role": "system", "content": "你是一个友好的助手，用一句话回答"},
                    {"role": "user", "content": "你好"}
                ],
                stream=False
            )
            reply = response['choices'][0]['message']['content']
            print(f"✅ 聊天测试成功: {reply}")
        except Exception as e:
            print(f"❌ 聊天测试失败: {e}")
            return False
        
        # TTS测试
        print("\n🎵 测试语音合成...")
        try:
            audio_data = await client.audio.speech.create(
                model="tts-1",
                input="你好，这是TkVoiceJourney的语音测试",
                voice="alloy"
            )
            
            if audio_data and len(audio_data) > 0:
                filename = "quick_demo_audio.mp3"
                with open(filename, "wb") as f:
                    f.write(audio_data)
                print(f"✅ TTS测试成功，音频已保存: {filename}")
            else:
                print("❌ TTS测试失败: 未生成音频数据")
                return False
                
        except Exception as e:
            print(f"❌ TTS测试失败: {e}")
            return False
        
        # 集成功能测试
        print("\n🎭 测试流式对话+TTS集成...")
        try:
            print("问题: 用一句话介绍人工智能")
            print("回答: ", end="", flush=True)
            
            stream = compatible_client.stream_chat_with_tts(
                user_input="用一句话介绍人工智能",
                system_prompt="你是一个AI专家，用简洁的语言回答",
                enable_tts=True
            )
            
            full_text = ""
            audio_data = None
            
            async for chunk in stream:
                if chunk['type'] == 'text':
                    print(chunk['content'], end="", flush=True)
                    full_text += chunk['content']
                elif chunk['type'] == 'audio':
                    import base64
                    audio_data = base64.b64decode(chunk['content'])
            
            if audio_data:
                filename = "integrated_demo_audio.mp3"
                with open(filename, "wb") as f:
                    f.write(audio_data)
                print(f"\n✅ 集成功能测试成功，音频已保存: {filename}")
            else:
                print("\n⚠️ 集成功能部分成功（文本正常，音频生成失败）")
                
        except Exception as e:
            print(f"\n❌ 集成功能测试失败: {e}")
            return False
        
        print("\n🎉 所有测试完成！系统运行正常")
        return True
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        return False


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "=" * 50)
        print("🎯 TkVoiceJourney 功能菜单")
        print("=" * 50)
        print("1. 🔍 查看配置状态")
        print("2. 🏥 健康检查")
        print("3. 🚀 快速演示")
        print("4. 💬 聊天测试")
        print("5. 🎵 TTS测试")
        print("6. 📖 查看使用说明")
        print("0. 🚪 退出")
        print("=" * 50)
        
        choice = input("请选择功能 (0-6): ").strip()
        
        if choice == '0':
            print("👋 感谢使用 TkVoiceJourney！")
            break
        elif choice == '1':
            print_config_status()
        elif choice == '2':
            asyncio.run(health_check_interactive())
        elif choice == '3':
            asyncio.run(quick_demo())
        elif choice == '4':
            asyncio.run(chat_test_interactive())
        elif choice == '5':
            asyncio.run(tts_test_interactive())
        elif choice == '6':
            show_usage_guide()
        else:
            print("❌ 无效选择，请重试")


async def health_check_interactive():
    """交互式健康检查"""
    try:
        client = OpenAICompatibleClient()
        health = await client.health_check()
        
        print(f"\n📊 健康状态: {health['status']}")
        print(f"📋 组件状态:")
        for component, status in health['components'].items():
            emoji = "✅" if status == "ok" else "❌"
            print(f"  {emoji} {component.upper()}: {status}")
        
        connections = client.test_connection()
        print(f"\n🔗 连接测试:")
        for service, status in connections.items():
            emoji = "✅" if status else "❌"
            print(f"  {emoji} {service.upper()}: {'连接正常' if status else '连接失败'}")
            
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")


async def chat_test_interactive():
    """交互式聊天测试"""
    print("\n💬 聊天测试 (输入 'quit' 退出)")
    
    try:
        client = OpenAI()
        
        while True:
            user_input = input("\n你: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not user_input:
                continue
                
            print("助手: ", end="", flush=True)
            
            try:
                stream = await client.chat.create(
                    messages=[
                        {"role": "system", "content": "你是一个友好的助手"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk['choices'][0]['delta'].get('content'):
                        print(chunk['choices'][0]['delta']['content'], end="", flush=True)
                print()
                
            except Exception as e:
                print(f"❌ 聊天失败: {e}")
                
    except Exception as e:
        print(f"❌ 初始化聊天客户端失败: {e}")


async def tts_test_interactive():
    """交互式TTS测试"""
    print("\n🎵 TTS测试 (输入 'quit' 退出)")
    
    try:
        client = OpenAI()
        
        while True:
            text_input = input("\n请输入要转换的文本: ").strip()
            if text_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not text_input:
                continue
                
            try:
                print("🔄 生成音频中...")
                audio_data = await client.audio.speech.create(
                    model="tts-1",
                    input=text_input,
                    voice="alloy"
                )
                
                if audio_data:
                    import time
                    filename = f"tts_test_{int(time.time())}.mp3"
                    with open(filename, "wb") as f:
                        f.write(audio_data)
                    print(f"✅ 音频已保存: {filename} ({len(audio_data)} 字节)")
                else:
                    print("❌ 音频生成失败")
                    
            except Exception as e:
                print(f"❌ TTS失败: {e}")
                
    except Exception as e:
        print(f"❌ 初始化TTS客户端失败: {e}")


def show_usage_guide():
    """显示使用指南"""
    print("\n📖 TkVoiceJourney 使用指南")
    print("=" * 50)
    print("""
🔧 配置要求:
1. 编辑根目录的 .env 文件
2. 配置必要的API密钥:
   - FISH_API_KEY (Fish Audio)
   - FISH_REFERENCE_ID (音色ID)
   - OPENAI_API_KEY (如果使用OpenAI)

📝 代码示例:

# 基础聊天
from src.core.openai_compatible import OpenAI
client = OpenAI()
response = await client.chat.create(
    messages=[{"role": "user", "content": "你好"}],
    stream=False
)

# 语音合成
audio = await client.audio.speech.create(
    model="tts-1",
    input="要转换的文本",
    voice="alloy"
)

🔄 LLM模式切换:
在 .env 文件中修改 LLM_MODE=openai 或 LLM_MODE=vllm

📚 更多信息请查看 README.md 文件
""")


async def main():
    """主函数"""
    print_banner()
    
    # 验证配置
    print("\n🔍 检查配置...")
    if not validate_config():
        print("\n❌ 配置验证失败，请按照以下步骤配置:")
        print("1. 编辑根目录的 .env 文件")
        print("2. 填入正确的API密钥")
        print("3. 重新运行此脚本")
        return
    
    print("✅ 配置验证通过")
    
    # 询问是否运行快速演示
    print("\n🤔 是否运行快速演示？")
    demo_choice = input("输入 'y' 运行演示，或任意键进入菜单: ").strip().lower()
    
    if demo_choice in ['y', 'yes', '是', 'Y']:
        success = await quick_demo()
        if success:
            print("\n🎉 快速演示完成！现在您可以:")
            print("1. 查看生成的音频文件")
            print("2. 参考 examples/openai_usage_example.py 学习更多用法")
            print("3. 阅读 README.md 了解详细功能")
    
    # 进入交互菜单
    interactive_menu()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用 TkVoiceJourney！")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc() 