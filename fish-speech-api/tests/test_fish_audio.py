#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fish Audio TTS 快速测试脚本
用于验证Fish Audio配置是否正确
"""

import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_fish_audio():
    """测试Fish Audio TTS功能"""
    print("🧪 Fish Audio TTS 快速测试")
    print("=" * 40)
    
    try:
        # 导入配置和客户端
        from config import validate_config, print_config_status
        from core.fish_websocket import FishWebSocketClient
        
        # 检查配置
        print("🔍 检查配置...")
        if not validate_config():
            print("❌ 配置验证失败")
            return False
        
        print("✅ 配置验证通过")
        
        # 显示配置状态
        print_config_status()
        
        # 创建客户端
        print("\n🎵 创建Fish Audio客户端...")
        client = FishWebSocketClient()
        
        # 测试连接
        print("🔗 测试连接...")
        if not client.test_connection():
            print("❌ 连接测试失败")
            print("\n可能的原因:")
            print("1. API Key无效")
            print("2. Reference ID错误")
            print("3. 网络连接问题")
            print("4. Fish Audio余额不足")
            return False
        
        print("✅ 连接测试成功")
        
        # 测试简单TTS
        print("\n🎤 测试语音合成...")
        test_text = "你好，这是Fish Audio的语音合成测试。如果你听到这段话，说明配置成功！"
        
        audio_data = await client.simple_tts(test_text)
        
        if audio_data and len(audio_data) > 0:
            # 保存音频文件
            output_file = "fish_audio_test.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            print(f"✅ 语音合成成功！")
            print(f"📁 音频已保存为: {output_file}")
            print(f"📊 音频大小: {len(audio_data)} 字节")
            
            # 尝试播放音频
            try:
                from core.audio_player import get_player
                player = get_player()
                print("🔊 开始播放音频...")
                player.play_audio_async(audio_data, "mp3")
                print("✅ 音频播放完成")
            except Exception as e:
                print(f"⚠️ 音频播放失败: {e}")
            
            return True
        else:
            print("❌ 语音合成失败，未生成音频数据")
            return False
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保在项目根目录运行此脚本")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    try:
        success = asyncio.run(test_fish_audio())
        
        print("\n" + "=" * 40)
        if success:
            print("🎉 Fish Audio 测试完成！")
            print("✅ 配置正确，可以正常使用")
            print("\n现在你可以:")
            print("1. 运行主应用: python run_app.py")
            print("2. 运行完整示例: python examples/openai_usage_example.py")
        else:
            print("❌ Fish Audio 测试失败")
            print("\n解决方案:")
            print("1. 检查 .env 文件中的 FISH_API_KEY")
            print("2. 检查 .env 文件中的 FISH_REFERENCE_ID")
            print("3. 访问 https://fish.audio 检查账户状态")
            print("4. 确保网络连接正常")
        
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"\n❌ 程序运行错误: {e}")


if __name__ == "__main__":
    main() 