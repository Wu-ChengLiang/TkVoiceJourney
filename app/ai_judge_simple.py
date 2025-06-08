#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版AI判断器
专注于弹幕价值判断，回复生成交给ai_reply.py处理
"""

import asyncio
import hashlib
import logging
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, AsyncIterator
from dataclasses import dataclass
from enum import Enum

from config import AI_JUDGE_CONFIG, HIGH_VALUE_KEYWORDS
from ai_reply import create_reply_generator

logger = logging.getLogger(__name__)


class ProcessAction(Enum):
    """处理动作枚举"""
    IGNORE = "ignore"
    PROCESS = "process"
    DEFER = "defer"
    BATCH = "batch"


@dataclass
class ProcessResult:
    """处理结果"""
    action: ProcessAction
    confidence: float = 0.0
    reason: str = ""
    delay: float = 0.0


@dataclass
class AIJudgeResult:
    """AI判断结果"""
    has_value: bool
    content: str
    reason: str
    category: str
    confidence: float = 0.0
    template_id: Optional[str] = None


class LRUCache:
    """简单的LRU缓存实现"""
    
    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.cache = {}
        self.access_order = deque()
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any):
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.maxsize:
            oldest = self.access_order.popleft()
            del self.cache[oldest]
        
        self.cache[key] = value
        self.access_order.append(key)
    
    def __contains__(self, key: str) -> bool:
        return key in self.cache


class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(self, capacity: int = 100, refill_rate: float = 10.0):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        tokens_to_add = (now - self.last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class KeywordFilter:
    """关键词过滤器"""
    
    def __init__(self):
        # 从配置文件加载关键词
        self.high_value_keywords = {}
        for category, keywords in HIGH_VALUE_KEYWORDS.items():
            for keyword in keywords:
                self.high_value_keywords[keyword] = 0.9
        
        # 负面关键词（降低价值）
        self.negative_keywords = {
            '哈哈': -0.5, '呵呵': -0.5, '嘿嘿': -0.5,
            '666': -0.5, '999': -0.5, '牛批': -0.3,
            '厉害': -0.3, '牛': -0.3, '棒': -0.3,
            '刷屏': -1.0, '广告': -1.0, '加群': -1.0,
            '推广': -1.0, '代理': -1.0, '招聘': -1.0
        }
        
        # 垃圾内容模式
        self.spam_patterns = [
            r'[0-9]{6,}',  # 长数字串
            r'[a-zA-Z]{10,}',  # 长字母串
            r'(.)\1{5,}',  # 重复字符
            r'[！!]{3,}',  # 多个感叹号
            r'[。.]{3,}',  # 多个句号
            r'http[s]?://',  # 网址
            r'QQ[:：]\s*\d+',  # QQ号
            r'微信[:：]',  # 微信号
        ]
    
    def calculate_score(self, content: str) -> float:
        """计算内容价值分数"""
        if not content or len(content.strip()) < 2:
            return 0.0
        
        content = content.strip().lower()
        
        # 检查垃圾内容
        if self._is_spam(content):
            return 0.0
        
        # 计算关键词得分
        score = 0.0
        
        # 高价值关键词
        for keyword, weight in self.high_value_keywords.items():
            if keyword in content:
                score += weight
        
        # 负面关键词
        for keyword, weight in self.negative_keywords.items():
            if keyword in content:
                score += weight
        
        # 长度调整
        length_bonus = min(0.2, len(content) / 100)
        score += length_bonus
        
        return max(0.0, min(1.0, score))
    
    def _is_spam(self, content: str) -> bool:
        """检查是否为垃圾内容"""
        for pattern in self.spam_patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def detect_category(self, content: str) -> str:
        """检测内容类别"""
        content = content.lower()
        
        for category, keywords in HIGH_VALUE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    return category
        
        return "其他"


class LocalClassifier:
    """本地轻量分类器"""
    
    def __init__(self):
        self.keyword_filter = KeywordFilter()
        
        # 问句模式
        self.question_patterns = [
            r'[？?]',  # 问号
            r'怎么[^0-9]*',  # 怎么开头
            r'什么[^0-9]*',  # 什么开头
            r'哪里[^0-9]*',  # 哪里开头
            r'几点[^0-9]*',  # 几点开头
            r'多少[^0-9]*',  # 多少开头
            r'可以.*吗',  # 可以...吗
            r'能.*吗',  # 能...吗
            r'有.*吗',  # 有...吗
        ]
    
    async def classify(self, content: str) -> float:
        """本地分类，返回置信度"""
        if not content:
            return 0.0
        
        # 基础关键词得分
        keyword_score = self.keyword_filter.calculate_score(content)
        
        # 问句模式得分
        question_score = self._calculate_question_score(content)
        
        # 综合得分
        final_score = keyword_score * 0.7 + question_score * 0.3
        
        return min(1.0, final_score)
    
    def _calculate_question_score(self, content: str) -> float:
        """计算问句得分"""
        score = 0.0
        for pattern in self.question_patterns:
            if re.search(pattern, content):
                score += 0.3
        return min(1.0, score)


class SmartBarrageProcessor:
    """智能弹幕预处理器"""
    
    def __init__(self):
        self.dedup_cache = LRUCache(maxsize=1000)
        self.keyword_filter = KeywordFilter()
        self.local_classifier = LocalClassifier()
        self.rate_limiter = TokenBucket(
            capacity=AI_JUDGE_CONFIG["rate_limit"]["capacity"],
            refill_rate=AI_JUDGE_CONFIG["rate_limit"]["refill_rate"]
        )
        self.processed_hashes = set()
        
        # 去重时间窗口
        self.dedup_window = 300  # 5分钟
    
    async def process_barrage(self, barrage: Dict) -> ProcessResult:
        """处理单条弹幕"""
        # 1. 基础过滤
        if not self._basic_filter(barrage):
            return ProcessResult(ProcessAction.IGNORE, reason="basic_filter")
        
        # 2. 去重检测
        if self._is_duplicate(barrage):
            return ProcessResult(ProcessAction.IGNORE, reason="duplicate")
        
        # 3. 高价值关键词强制处理
        content = barrage.get('content', '')
        high_value_keywords = [
            '测试', '咨询', '预约', '价格', '多少钱', '营业时间', '地址', '电话', '怎么',
            '链接', '套餐', '元', '包含', '荤', '素', '主食', '锅底', '蘸料', '门店',
            '双人餐', '三人餐', '四人餐', '全国', '导航', '今天拍'
        ]
        if any(kw in content for kw in high_value_keywords):
            return ProcessResult(ProcessAction.PROCESS, confidence=1.0, reason="high_value_keyword_match")
        
        # 4. 关键词预筛选
        keyword_score = self.keyword_filter.calculate_score(content)
        if keyword_score < AI_JUDGE_CONFIG["keyword_threshold"]:
            return ProcessResult(ProcessAction.IGNORE, reason="low_keyword_score")
        
        # 5. 本地轻量分类
        local_score = await self.local_classifier.classify(content)
        if local_score < AI_JUDGE_CONFIG["local_score_threshold"]:
            return ProcessResult(ProcessAction.IGNORE, reason="low_local_score")
        
        # 6. 频率控制
        if not self.rate_limiter.consume(1):
            return ProcessResult(ProcessAction.DEFER, reason="rate_limit", delay=2.0)
        
        # 7. 决定处理策略
        if local_score > 0.8:
            return ProcessResult(ProcessAction.PROCESS, confidence=local_score)
        else:
            return ProcessResult(ProcessAction.BATCH, confidence=local_score)
    
    def _basic_filter(self, barrage: Dict) -> bool:
        """基础过滤"""
        # 检查类型
        if barrage.get('type') not in ['chat', 'emoji_chat']:
            return False
        
        # 检查内容
        content = barrage.get('content', '').strip()
        if not content or len(content) < 2 or len(content) > 500:  # 增加最大长度限制
            return False
        
        # 检查是否为纯表情
        if self._is_pure_emoji(content):
            return False
        
        return True
    
    def _is_duplicate(self, barrage: Dict) -> bool:
        """去重检测"""
        content = barrage.get('content', '')
        user_id = barrage.get('user_id', '')
        
        # 生成去重key
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = barrage.get('timestamp', time.time())
        
        # 检查内容去重
        content_key = f"content_{content_hash}"
        if content_key in self.dedup_cache:
            last_time = self.dedup_cache.get(content_key)
            if timestamp - last_time < self.dedup_window:
                return True
        
        # 检查用户去重
        user_key = f"user_{user_id}_{content_hash}"
        if user_key in self.dedup_cache:
            return True
        
        # 记录
        self.dedup_cache.put(content_key, timestamp)
        self.dedup_cache.put(user_key, timestamp)
        
        return False
    
    def _is_pure_emoji(self, content: str) -> bool:
        """检查是否为纯表情"""
        # 简单的表情检测
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
        text_without_emoji = re.sub(emoji_pattern, '', content)
        return len(text_without_emoji.strip()) == 0


class StreamingReplyProcessor:
    """流式回复处理器（结合AI回复生成器）"""
    
    def __init__(self):
        self.reply_generator = create_reply_generator()
        self.current_sessions = {}
    
    async def generate_reply_stream(self, content: str) -> AsyncIterator[str]:
        """生成流式回复"""
        try:
            async for part in self.reply_generator.generate_reply_stream(content):
                yield part
                
        except Exception as e:
            logger.error(f"流式回复生成失败: {e}")
            yield "稍等哦，小助理马上去通知店家确认~"
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """生成完整回复"""
        try:
            result = await self.reply_generator.generate_reply(content)
            return result.text if result else None
            
        except Exception as e:
            logger.error(f"回复生成失败: {e}")
            return "稍等哦，小助理马上去通知店家确认~"
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.reply_generator.get_stats()
    
    async def close(self):
        """关闭资源"""
        await self.reply_generator.close()


class OptimizedAIJudge:
    """优化版AI判断器（使用新的架构）"""
    
    def __init__(self):
        self.preprocessor = SmartBarrageProcessor()
        self.reply_processor = StreamingReplyProcessor()
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'ignored_count': 0,
            'ai_calls': 0,
            'cache_hits': 0,
            'batch_processed': 0,
            'template_replies': 0,
            'stream_replies': 0
        }
    
    async def process_barrage_stream(self, barrage: Dict) -> Optional[str]:
        """处理弹幕流"""
        self.stats['total_processed'] += 1
        
        # 增加调试信息
        content = barrage.get('content', '')[:50]
        msg_type = barrage.get('type', 'unknown')
        logger.debug(f"🔍 处理弹幕 [{msg_type}]: {content}...")
        
        # 预处理
        result = await self.preprocessor.process_barrage(barrage)
        
        if result.action == ProcessAction.IGNORE:
            self.stats['ignored_count'] += 1
            logger.debug(f"❌ 忽略弹幕: {result.reason}")
            return None
        
        elif result.action == ProcessAction.PROCESS:
            # 立即处理
            logger.info(f"🚀 立即处理弹幕 (置信度: {result.confidence:.2f}): {content}")
            return await self._immediate_process(barrage)
        
        elif result.action == ProcessAction.BATCH:
            # 批处理（暂时简化为立即处理）
            self.stats['batch_processed'] += 1
            logger.debug(f"📦 批处理弹幕 (置信度: {result.confidence:.2f}): {content}")
            return await self._immediate_process(barrage)
        
        elif result.action == ProcessAction.DEFER:
            # 延迟处理
            logger.debug(f"⏰ 延迟处理 {result.delay}秒: {content}")
            await asyncio.sleep(result.delay)
            return await self._immediate_process(barrage)
        
        return None
    
    async def _immediate_process(self, barrage: Dict) -> Optional[str]:
        """立即处理弹幕"""
        try:
            content = barrage.get('content', '')
            
            # 生成回复
            self.stats['ai_calls'] += 1
            reply = await self.reply_processor.generate_reply(content)
            
            if reply:
                logger.info(f"✅ 生成回复: {reply}")
                return reply
            
        except Exception as e:
            logger.error(f"立即处理失败: {e}")
        
        return None
    
    async def generate_reply_stream(self, content: str) -> AsyncIterator[str]:
        """生成流式回复"""
        self.stats['stream_replies'] += 1
        async for part in self.reply_processor.generate_reply_stream(content):
            yield part
    
    async def judge_barrages(self, barrages: List[Dict]) -> Optional[Dict]:
        """兼容原接口的判断方法"""
        if not barrages:
            return None
        
        # 使用新的处理流程
        for barrage in barrages:
            result = await self.process_barrage_stream(barrage)
            if result:
                category = self.preprocessor.keyword_filter.detect_category(barrage.get('content', ''))
                return {
                    'has_value': True,
                    'content': barrage.get('content', ''),
                    'reason': '通过优化流程判断',
                    'category': category
                }
        
        return None
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """兼容原接口的回复生成方法"""
        return await self.reply_processor.generate_reply(content)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        # 合并所有统计信息
        reply_stats = self.reply_processor.get_stats()
        return {
            **self.stats,
            **reply_stats
        }
    
    async def close(self):
        """关闭资源"""
        await self.reply_processor.close()


# 工厂函数
def create_ai_judge():
    """创建AI判断器实例"""
    try:
        return OptimizedAIJudge()
    except Exception as e:
        logger.error(f"创建AI判断器失败: {e}")
        return None


if __name__ == "__main__":
    # 测试代码
    async def test():
        judge = create_ai_judge()
        if not judge:
            print("判断器创建失败")
            return
        
        test_barrages = [
            {"type": "chat", "content": "请问你们的菜品价格多少钱", "user": "test1", "timestamp": time.time()},
            {"type": "chat", "content": "666", "user": "test2", "timestamp": time.time()},
            {"type": "chat", "content": "我想预约位置", "user": "test3", "timestamp": time.time()},
            {"type": "chat", "content": "你们地址在哪里", "user": "test4", "timestamp": time.time()},
        ]
        
        for barrage in test_barrages:
            print(f"\n弹幕: {barrage['content']}")
            
            # 测试普通回复
            result = await judge.process_barrage_stream(barrage)
            print(f"回复: {result}")
            
            # 测试流式回复
            if result:
                print("流式: ", end="")
                async for part in judge.generate_reply_stream(barrage['content']):
                    print(part, end="", flush=True)
                print()
        
        print(f"\n统计信息: {judge.get_stats()}")
        await judge.close()
    
    asyncio.run(test()) 