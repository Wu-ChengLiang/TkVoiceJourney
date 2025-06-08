#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI判断器测试脚本
测试多层过滤、智能批处理和AI调用功能
"""

import asyncio
import time
from ai_judge import create_ai_judge

# 测试弹幕数据
TEST_BARRAGES = [
    # 高价值弹幕
    {"type": "chat", "content": "请问你们的中医理疗多少钱？", "user": "[12345]张三", "user_id": "12345", "timestamp": time.time()},
    {"type": "chat", "content": "我想预约针灸治疗", "user": "[67890]李四", "user_id": "67890", "timestamp": time.time()},
    {"type": "chat", "content": "你们营业时间是几点到几点？", "user": "[11111]王五", "user_id": "11111", "timestamp": time.time()},
    {"type": "chat", "content": "地址在哪里？怎么走？", "user": "[22222]赵六", "user_id": "22222", "timestamp": time.time()},
    
    # 中等价值弹幕
    {"type": "chat", "content": "可以治疗颈椎病吗？", "user": "[33333]孙七", "user_id": "33333", "timestamp": time.time()},
    {"type": "chat", "content": "怎么联系你们？", "user": "[44444]周八", "user_id": "44444", "timestamp": time.time()},
    
    # 低价值弹幕
    {"type": "chat", "content": "666", "user": "[55555]吴九", "user_id": "55555", "timestamp": time.time()},
    {"type": "chat", "content": "哈哈哈", "user": "[66666]郑十", "user_id": "66666", "timestamp": time.time()},
    {"type": "chat", "content": "主播好棒！", "user": "[77777]观众甲", "user_id": "77777", "timestamp": time.time()},
    
    # 垃圾弹幕
    {"type": "chat", "content": "1234567890", "user": "[88888]刷屏者", "user_id": "88888", "timestamp": time.time()},
    {"type": "chat", "content": "加群加群加群", "user": "[99999]广告", "user_id": "99999", "timestamp": time.time()},
    
    # 重复弹幕
    {"type": "chat", "content": "请问你们的中医理疗多少钱？", "user": "[12345]张三", "user_id": "12345", "timestamp": time.time()},
]

async def test_ai_judge():
    """测试AI判断器"""
    print("🧪 开始测试AI判断器...")
    
    # 创建AI判断器
    judge = create_ai_judge()
    
    print(f"📊 AI判断器类型: {type(judge).__name__}")
    
    # 测试单条弹幕处理
    print("\n=== 测试单条弹幕处理 ===")
    
    for i, barrage in enumerate(TEST_BARRAGES):
        print(f"\n🔍 测试弹幕 {i+1}: {barrage['content']}")
        
        if hasattr(judge, 'process_barrage_stream'):
            # 使用优化版处理
            reply = await judge.process_barrage_stream(barrage)
            if reply:
                print(f"✅ AI回复: {reply}")
            else:
                print("❌ 弹幕被过滤或无回复")
        else:
            # 使用简化版处理
            result = await judge.judge_barrages([barrage])
            if result and result.get('has_value'):
                reply = await judge.generate_reply(result.get('content'))
                print(f"✅ AI回复: {reply}")
            else:
                print("❌ 弹幕无价值或处理失败")
    
    # 测试批量处理
    print("\n=== 测试批量处理 ===")
    
    high_value_barrages = TEST_BARRAGES[:4]  # 前4条高价值弹幕
    
    if hasattr(judge, 'judge_barrages'):
        result = await judge.judge_barrages(high_value_barrages)
        if result and result.get('has_value'):
            reply = await judge.generate_reply(result.get('content'))
            print(f"✅ 批量处理结果: {reply}")
        else:
            print("❌ 批量处理无结果")
    
    # 显示统计信息
    if hasattr(judge, 'get_stats'):
        stats = judge.get_stats()
        print("\n=== AI判断器统计信息 ===")
        for key, value in stats.items():
            print(f"📈 {key}: {value}")
    
    # 关闭资源
    await judge.close()
    print("\n✅ 测试完成")

async def test_performance():
    """测试性能"""
    print("\n🚀 开始性能测试...")
    
    judge = create_ai_judge()
    
    # 测试大量弹幕处理
    start_time = time.time()
    processed_count = 0
    reply_count = 0
    
    for i in range(100):  # 处理100条弹幕
        barrage = {
            "type": "chat", 
            "content": f"测试弹幕{i}: 请问价格多少？", 
            "user": f"[{i}]测试用户{i}", 
            "user_id": str(i),
            "timestamp": time.time()
        }
        
        if hasattr(judge, 'process_barrage_stream'):
            reply = await judge.process_barrage_stream(barrage)
            processed_count += 1
            if reply:
                reply_count += 1
        
        # 每10条显示一次进度
        if (i + 1) % 10 == 0:
            print(f"📊 已处理: {i+1}/100")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️ 性能测试结果:")
    print(f"📈 总处理时间: {duration:.2f}秒")
    print(f"📈 处理速度: {processed_count/duration:.2f}条/秒")
    print(f"📈 回复生成率: {reply_count/processed_count*100:.1f}%")
    
    # 显示最终统计
    if hasattr(judge, 'get_stats'):
        stats = judge.get_stats()
        print(f"📈 最终统计: {stats}")
    
    await judge.close()

if __name__ == "__main__":
    print("🎯 AI判断器测试程序")
    print("=" * 50)
    
    # 运行功能测试
    asyncio.run(test_ai_judge())
    
    # 运行性能测试
    asyncio.run(test_performance())
    
    print("\n🎉 所有测试完成！") 