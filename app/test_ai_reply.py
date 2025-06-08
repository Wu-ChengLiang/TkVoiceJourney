#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI回复系统
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai_judge_simple import create_ai_judge
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_ai_judge():
    """测试AI判断器"""
    print("🔧 初始化AI判断器...")
    
    judge = create_ai_judge()
    if not judge:
        print("❌ AI判断器创建失败")
        return
    
    print("✅ AI判断器创建成功")
    
    # 测试弹幕数据（模拟真实弹幕格式）
    test_barrages = [
        {
            "type": "chat",
            "content": "4号链接107.9元3-4人套餐肉多的离谱包含10荤4素1主食锅底蘸料",
            "user": "笑笑来了",
            "user_id": "82020492603",
            "timestamp": time.time()
        },
        {
            "type": "chat", 
            "content": "请问你们营业时间是几点到几点？",
            "user": "顾客A",
            "user_id": "123456",
            "timestamp": time.time()
        },
        {
            "type": "chat",
            "content": "666",
            "user": "路人",
            "user_id": "789012", 
            "timestamp": time.time()
        },
        {
            "type": "chat",
            "content": "1号链接双人餐55包含5荤4素1主食包含蘸料锅底、无隐藏消费",
            "user": "笑笑来了",
            "user_id": "82020492603",
            "timestamp": time.time()
        },
        {
            "type": "chat",
            "content": "想预约明天晚上的位置",
            "user": "顾客B", 
            "user_id": "345678",
            "timestamp": time.time()
        }
    ]
    
    print(f"\n🧪 测试 {len(test_barrages)} 条弹幕:")
    
    for i, barrage in enumerate(test_barrages, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"内容: {barrage['content']}")
        print(f"类型: {barrage['type']}")
        print(f"用户: {barrage['user']}")
        
        try:
            # 测试新的流式处理接口
            if hasattr(judge, 'process_barrage_stream'):
                reply = await judge.process_barrage_stream(barrage)
                if reply:
                    print(f"✅ AI回复: {reply}")
                else:
                    print("❌ 无回复（可能被过滤）")
            
            # 测试传统接口
            elif hasattr(judge, 'judge_barrages'):
                result = await judge.judge_barrages([barrage])
                if result and result.get('has_value'):
                    reply = await judge.generate_reply(result.get('content', ''))
                    print(f"✅ AI回复: {reply}")
                else:
                    print("❌ 无回复（可能被过滤）")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 打印统计信息
    if hasattr(judge, 'get_stats'):
        stats = judge.get_stats()
        print(f"\n📊 统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # 清理资源
    if hasattr(judge, 'close'):
        await judge.close()
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_ai_judge()) 