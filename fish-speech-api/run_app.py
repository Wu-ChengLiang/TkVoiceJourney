#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TkVoiceJourney 应用启动脚本
简洁的语音聊天应用 - 支持vLLM + Fish Audio TTS
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """主启动函数"""
    print("🎵 TkVoiceJourney - 语音聊天系统")
    print("=" * 50)
    
    try:
        # 导入并运行简洁应用
        from gui.simple_chat_app import main as app_main
        print("🚀 启动简洁语音聊天应用...")
        app_main()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖:")
        print("  pip install -r requirements.txt")
        print("\n请检查配置:")
        print("1. 编辑根目录的 .env 文件")
        print("2. 配置 FISH_API_KEY 和 FISH_REFERENCE_ID")
        print("3. 配置 OPENAI_API_KEY (如果使用OpenAI模式)")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n故障排除:")
        print("1. 运行配置检查: python src/config.py")
        print("2. 运行快速测试: python quick_start.py")
        print("3. 检查网络连接和API密钥")


if __name__ == "__main__":
    main() 