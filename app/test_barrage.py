#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弹幕测试模块 - 用于模拟弹幕数据进行测试
"""

import asyncio
import random
import time
from typing import Callable, Optional

class TestBarrageFetcher:
    """测试用弹幕获取器"""
    
    def __init__(self, live_id: str):
        self.live_id = live_id
        self.callback: Optional[Callable] = None
        self.running = False
        
        # 模拟弹幕数据
        self.test_barrages = [
            {
                'type': 'chat',
                'user_id': '123456789',
                'username': '美食爱好者',
                'content': '有什么好吃的推荐吗？',
                'user': '[123456789]美食爱好者',
                'raw_type': '聊天msg'
            },
            {
                'type': 'chat',
                'user_id': '987654321',
                'username': '健康达人',
                'content': '你们的中医理疗怎么预约？',
                'user': '[987654321]健康达人',
                'raw_type': '聊天msg'
            },
            {
                'type': 'member',
                'user_id': '111222333',
                'username': '新用户',
                'gender': '女',
                'content': '进入了直播间',
                'user': '[111222333][女]新用户',
                'raw_type': '进场msg'
            },
            {
                'type': 'chat',
                'user_id': '444555666',
                'username': '老顾客',
                'content': '营业时间是几点到几点？',
                'user': '[444555666]老顾客',
                'raw_type': '聊天msg'
            },
            {
                'type': 'gift',
                'user_id': '777888999',
                'username': '礼物达人',
                'gift_name': '小心心',
                'gift_count': 5,
                'content': '送出 小心心 x5',
                'user': '[777888999]礼物达人',
                'raw_type': '礼物msg'
            },
            {
                'type': 'chat',
                'user_id': '123123123',
                'username': '咨询者',
                'content': '可以现场体验吗？需要预约吗？',
                'user': '[123123123]咨询者',
                'raw_type': '聊天msg'
            },
            {
                'type': 'like',
                'user_id': '456456456',
                'username': '点赞用户',
                'like_count': 10,
                'content': '点赞 x10',
                'user': '[456456456]点赞用户',
                'raw_type': '点赞msg'
            },
            {
                'type': 'stats',
                'display_viewers': random.randint(10, 50),
                'content': f'{random.randint(10, 50)}在线观众',
                'user': '系统统计',
                'raw_type': '直播间统计msg'
            },
            {
                'type': 'chat',
                'user_id': '789789789',
                'username': '价格询问者',
                'content': '理疗一次多少钱啊？',
                'user': '[789789789]价格询问者',
                'raw_type': '聊天msg'
            },
            {
                'type': 'follow',
                'user_id': '321321321',
                'username': '新关注',
                'content': '关注了主播',
                'user': '[321321321]新关注',
                'raw_type': '关注msg'
            }
        ]
        
    def set_callback(self, callback: Callable):
        """设置弹幕回调函数"""
        self.callback = callback
        
    async def start(self):
        """开始模拟弹幕"""
        if self.running:
            return
            
        self.running = True
        print(f"🧪 开始模拟直播间 {self.live_id} 的弹幕")
        
        # 模拟弹幕流
        while self.running:
            # 随机选择弹幕
            barrage = random.choice(self.test_barrages).copy()
            
            # 添加时间戳
            barrage['timestamp'] = time.time()
            
            # 随机修改一些内容
            if barrage['type'] == 'stats':
                barrage['display_viewers'] = random.randint(10, 50)
                barrage['content'] = f"{barrage['display_viewers']}在线观众"
            
            # 调用回调函数
            if self.callback:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(barrage)
                    else:
                        self.callback(barrage)
                except Exception as e:
                    print(f"回调函数执行失败: {e}")
            
            # 随机间隔
            await asyncio.sleep(random.uniform(2, 8))
    
    async def stop(self):
        """停止模拟弹幕"""
        self.running = False
        print("🛑 停止弹幕模拟")


# 使用测试弹幕获取器替换原有的
def use_test_fetcher():
    """使用测试弹幕获取器"""
    import sys
    from pathlib import Path
    
    # 替换导入
    app_path = Path(__file__).parent
    if str(app_path) not in sys.path:
        sys.path.insert(0, str(app_path))
    
    # 替换barrage_fetcher模块中的BarrageFetcher
    import barrage_fetcher
    barrage_fetcher.BarrageFetcher = TestBarrageFetcher
    
    print("🧪 已启用测试弹幕模式")


async def generate_test_barrages(callback):
    """生成持续的测试弹幕数据"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 启动测试弹幕生成器")
    
    # 测试弹幕数据
    TEST_BARRAGES = [
        {
            'type': 'chat',
            'user_id': '123456789',
            'username': '美食爱好者',
            'content': '有什么好吃的推荐吗？',
            'user': '[123456789]美食爱好者',
            'raw_type': '聊天msg'
        },
        {
            'type': 'chat',
            'user_id': '987654321',
            'username': '健康达人',
            'content': '你们的中医理疗怎么预约？',
            'user': '[987654321]健康达人',
            'raw_type': '聊天msg'
        },
        {
            'type': 'member',
            'user_id': '111222333',
            'username': '新用户',
            'gender': '女',
            'content': '进入了直播间',
            'user': '[111222333][女]新用户',
            'raw_type': '进场msg'
        },
        {
            'type': 'chat',
            'user_id': '444555666',
            'username': '老顾客',
            'content': '营业时间是几点到几点？',
            'user': '[444555666]老顾客',
            'raw_type': '聊天msg'
        },
        {
            'type': 'gift',
            'user_id': '777888999',
            'username': '礼物达人',
            'gift_name': '小心心',
            'gift_count': 5,
            'content': '送出 小心心 x5',
            'user': '[777888999]礼物达人',
            'raw_type': '礼物msg'
        }
    ]
    
    count = 0
    while count < 50:  # 生成50条测试弹幕
        try:
            # 随机选择一条测试弹幕
            barrage = random.choice(TEST_BARRAGES).copy()
            
            # 添加随机变化
            if barrage['type'] == 'chat':
                # 随机修改聊天内容
                contents = [
                    barrage['content'],
                    "这个产品怎么样？",
                    "价格多少钱？",
                    "可以预约吗？",
                    "营业时间是什么时候？",
                    "有什么优惠吗？",
                    "效果好不好？"
                ]
                barrage['content'] = random.choice(contents)
            
            # 随机用户ID和昵称
            barrage['user_id'] = str(random.randint(10000000, 99999999))
            barrage['username'] = f"用户{random.randint(1000, 9999)}"
            barrage['user'] = f"[{barrage['user_id']}]{barrage['username']}"
            
            # 添加时间戳
            barrage['timestamp'] = time.time()
            
            # 调用回调函数
            await callback(barrage)
            count += 1
            
            # 随机间隔（1-3秒）
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            logger.error(f"生成测试弹幕失败: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    # 测试模式
    async def test_callback(barrage_data):
        print(f"收到弹幕: {barrage_data}")
    
    fetcher = TestBarrageFetcher("test_room")
    fetcher.set_callback(test_callback)
    
    try:
        await fetcher.start()
    except KeyboardInterrupt:
        await fetcher.stop()
        print("测试结束") 