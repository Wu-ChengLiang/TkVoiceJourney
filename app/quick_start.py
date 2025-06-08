#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本
帮助用户快速测试AI判断器功能
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查.env文件
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ 未找到.env文件")
        print("📝 请复制.env.example到.env并配置API Key")
        return False
    
    # 检查API Key
    api_key = os.getenv("AI_API_KEY", "")
    if not api_key or api_key == "sk-your-api-key-here":
        print("❌ 未配置有效的AI API Key")
        print("📝 请在.env文件中设置AI_API_KEY")
        return False
    
    print("✅ 环境配置检查通过")
    print(f"🔑 API类型: {os.getenv('AI_API_TYPE', 'openai')}")
    print(f"🤖 模型: {os.getenv('AI_MODEL_NAME', 'gpt-4o-mini')}")
    return True

async def test_ai_judge():
    """测试AI判断器"""
    print("\n🧪 测试AI判断器...")
    
    try:
        from ai_judge import create_ai_judge
        
        # 创建AI判断器
        judge = create_ai_judge()
        print(f"📊 AI判断器类型: {type(judge).__name__}")
        
        # 测试弹幕
        test_barrage = {
            "type": "chat",
            "content": "请问你们的中医理疗多少钱？",
            "user": "[12345]测试用户",
            "user_id": "12345",
            "timestamp": 1234567890
        }
        
        print(f"🔍 测试弹幕: {test_barrage['content']}")
        
        # 处理弹幕
        if hasattr(judge, 'process_barrage_stream'):
            reply = await judge.process_barrage_stream(test_barrage)
            if reply:
                print(f"✅ AI回复: {reply}")
            else:
                print("❌ 弹幕被过滤或无回复")
        else:
            result = await judge.judge_barrages([test_barrage])
            if result and result.get('has_value'):
                reply = await judge.generate_reply(result.get('content'))
                print(f"✅ AI回复: {reply}")
            else:
                print("❌ 弹幕无价值")
        
        # 显示统计
        if hasattr(judge, 'get_stats'):
            stats = judge.get_stats()
            print(f"📈 统计信息: {stats}")
        
        await judge.close()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def start_main_app():
    """启动主应用"""
    print("\n🚀 启动主应用...")
    print("📱 Web界面将在 http://localhost:8000 启动")
    print("🛑 按 Ctrl+C 停止服务")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("🎯 抖音直播弹幕语音客服系统 - 快速启动")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("\n💡 配置步骤:")
        print("1. 复制 .env.example 到 .env")
        print("2. 在 .env 中设置您的 AI_API_KEY")
        print("3. 重新运行此脚本")
        return
    
    # 测试AI判断器
    test_result = asyncio.run(test_ai_judge())
    
    if test_result:
        print("\n✅ AI判断器测试通过！")
        
        # 询问是否启动主应用
        choice = input("\n🤔 是否启动主应用？(y/n): ").lower().strip()
        if choice in ['y', 'yes', '是']:
            start_main_app()
        else:
            print("👋 感谢使用！")
    else:
        print("\n❌ AI判断器测试失败")
        print("💡 请检查API配置和网络连接")

if __name__ == "__main__":
    main() 