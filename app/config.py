#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# OpenAI 配置
OPENAI_CONFIG = {
    "api_key": os.getenv("AI_API_KEY", ""),
    "api_base": os.getenv("AI_API_BASE", "https://api.openai.com/v1"),
    "model": os.getenv("AI_MODEL_NAME", "gpt-4o-mini"),
    "temperature": 0.7,
    "max_tokens": 150,
    "stream": True  # 启用流式输出
}

# Fish Audio TTS 配置
FISH_AUDIO_CONFIG = {
    "api_key": os.getenv("FISH_AUDIO_API_KEY", "c519c7c1b9a249069c078110c9ed4af9"),
    "websocket_url": "wss://api.fish.audio/v1/tts/live",
    "voice_id": "57eab548c7ed4ddc974c4c153cb015b2",  # 指定的声音ID
    "model": "speech-1.6",  # 使用最新模型
    "format": "opus",  # 音频格式
    "latency": "normal",  # 延迟模式
    "temperature": 0.7,
    "top_p": 0.7,
    "prosody": {
        "speed": 1.0,  # 语速
        "volume": 0    # 音量
    }
}

# 餐厅业务配置
RESTAURANT_CONFIG = {
    "name": "美味餐厅",
    "cuisine_type": "川菜",
    "services": ["堂食", "外卖", "团购"],
    "avg_price": "68",
    "business_hours": "10:00-22:00",
    "phone": "400-xxx-xxxx",
    "features": ["麻辣香锅", "水煮鱼", "口水鸡", "毛血旺"]
}

# AI判断器配置
AI_JUDGE_CONFIG = {
    "keyword_threshold": 0.05,
    "local_score_threshold": 0.2,
    "batch_size": 3,
    "max_wait_time": 10.0,
    "rate_limit": {
        "capacity": 50,
        "refill_rate": 5.0
    },
    "cost_limit": {
        "daily_budget": 10.0,
        "cost_per_call": 0.002
    }
}

# 固定模板回复
TEMPLATE_REPLIES = {
    "预约": [
        "宝子想订几人位呀？周末建议提前2天预约哦~ 🌸",
        "亲，预约请说明几位几点，小助理马上帮您安排~ ✨",
        "预约的话，建议提前1-2天哦，热门时段很抢手呢~ 💕"
    ],
    "价格": [
        "人均xx元起，性价比超高！宝子可以看看我们的团购套餐~ 🎉",
        "价格很实惠哦，团购更优惠！具体可以看直播间链接~ 💰",
        "我们有多种价位套餐，xx元起就能吃得很满足~ 😋"
    ],
    "营业时间": [
        "营业时间：10:00-22:00，全天为您服务~ ⏰",
        "早10点到晚10点都营业哦，欢迎随时来~ 🕙",
        "10:00-22:00营业，午市晚市都有不同优惠~ ⭐"
    ],
    "地址": [
        "门店地址导航搜xx就能找到，有停车位哦~ 🚗",
        "具体地址xx，地铁xx站出来就到，很方便~ 🚇",
        "地址在xx，可以导航过来，有多个停车场~ 📍"
    ],
    "菜品推荐": [
        "招牌必点：麻辣香锅、水煮鱼！宝子一定要试试~ 🔥",
        "爆款菜品推荐：口水鸡、毛血旺，回头客最爱~ 🌶️",
        "特色招牌xx，每桌必点，超级下饭~ 🍚"
    ],
    "外卖": [
        "外卖可以xx平台下单，30分钟内送达~ 🛵",
        "支持外卖配送，保温包装，味道不打折~ 📦",
        "外卖服务覆盖xx公里，新用户还有折扣~ 🎁"
    ],
    "默认": [
        "感谢宝子的咨询，有什么问题尽管问小助理~ 💖",
        "亲，有任何疑问都可以私信哦，小助理随时在线~ 🌟",
        "稍等哦，小助理马上去通知店家确认~ 🏃‍♀️"
    ]
}

# 高价值关键词配置
HIGH_VALUE_KEYWORDS = {
    '预约': ['预约', '订位', '订桌', '定位', '定桌', '挂号'],
    '价格': ['价格', '多少钱', '费用', '收费', '人均', '消费', '团购', '优惠'],
    '营业时间': ['营业时间', '上班时间', '几点', '什么时候', '开门', '关门'],
    '地址': ['地址', '位置', '在哪', '怎么走', '导航', '路线'],
    '菜品推荐': ['推荐', '招牌', '特色', '好吃', '必点', '什么菜', '菜品'],
    '外卖': ['外卖', '送餐', '配送', '叫餐', '打包'],
    '电话': ['电话', '联系', '微信', '客服']
} 