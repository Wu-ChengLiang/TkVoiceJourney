#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI判断模块 - 优化版本
基于多层过滤漏斗架构，实现智能弹幕价值判断和回复生成
包含预过滤、去重、本地分类、AI判断、批处理等功能
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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


class CostTracker:
    """成本追踪器"""
    
    def __init__(self, daily_budget: float = 10.0):
        self.daily_budget = daily_budget
        self.daily_cost = 0.0
        self.last_reset = datetime.now().date()
        self.cost_per_call = 0.002  # 估算每次API调用成本(美元)
    
    def record_call(self, cost: float = None):
        """记录API调用成本"""
        self._check_reset()
        cost = cost or self.cost_per_call
        self.daily_cost += cost
    
    def within_budget(self) -> bool:
        """检查是否在预算内"""
        self._check_reset()
        return self.daily_cost < self.daily_budget
    
    def _check_reset(self):
        """检查是否需要重置日成本"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_cost = 0.0
            self.last_reset = today


class KeywordFilter:
    """关键词过滤器"""
    
    def __init__(self):
        # 高价值关键词
        self.high_value_keywords = {
            '咨询': 1.0, '预约': 1.0, '挂号': 1.0, '看病': 1.0,
            '价格': 0.9, '多少钱': 0.9, '费用': 0.9, '收费': 0.9,
            '营业时间': 0.8, '上班时间': 0.8, '几点': 0.8,
            '地址': 0.8, '位置': 0.8, '在哪': 0.8, '怎么走': 0.8,
            '电话': 0.7, '联系': 0.7, '微信': 0.7,
            '治疗': 0.9, '调理': 0.9, '中医': 0.8, '针灸': 0.8,
            '推拿': 0.8, '理疗': 0.8, '按摩': 0.8,
            '怎么': 0.6, '可以': 0.5, '能不能': 0.6, '行不行': 0.6
        }
        
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
        self.rate_limiter = TokenBucket(capacity=50, refill_rate=5.0)
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
        
        # 3. 关键词预筛选
        content = barrage.get('content', '')
        keyword_score = self.keyword_filter.calculate_score(content)
        if keyword_score < 0.1:
            return ProcessResult(ProcessAction.IGNORE, reason="low_keyword_score")
        
        # 4. 本地轻量分类
        local_score = await self.local_classifier.classify(content)
        if local_score < 0.3:
            return ProcessResult(ProcessAction.IGNORE, reason="low_local_score")
        
        # 5. 频率控制
        if not self.rate_limiter.consume(1):
            return ProcessResult(ProcessAction.DEFER, reason="rate_limit", delay=2.0)
        
        # 6. 决定处理策略
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
        if not content or len(content) < 2 or len(content) > 200:
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


class SmartBatchProcessor:
    """智能批处理器"""
    
    def __init__(self, ai_judge):
        self.ai_judge = ai_judge
        self.batch_size = 5
        self.max_wait_time = 10.0
        self.current_batch = []
        self.last_process_time = time.time()
        self.processing_lock = asyncio.Lock()
    
    async def add_to_batch(self, barrage: Dict) -> Optional[str]:
        """添加到批处理队列"""
        async with self.processing_lock:
            self.current_batch.append(barrage)
            
            # 触发条件
            should_process = (
                len(self.current_batch) >= self.batch_size or
                time.time() - self.last_process_time > self.max_wait_time
            )
            
            if should_process:
                return await self._process_batch()
        
        return None
    
    async def _process_batch(self) -> Optional[str]:
        """处理当前批次"""
        if not self.current_batch:
            return None
        
        try:
            # 批量AI判断
            batch_results = await self.ai_judge.batch_judge_barrages(self.current_batch)
            
            # 找到最高价值的结果
            best_result = None
            best_score = 0.0
            
            for result in batch_results:
                if result and result.has_value and result.confidence > best_score:
                    best_result = result
                    best_score = result.confidence
            
            if best_result:
                reply = await self.ai_judge.generate_reply(best_result.content)
                self.current_batch.clear()
                self.last_process_time = time.time()
                return reply
            
        except Exception as e:
            logger.error(f"批处理失败: {e}")
        
        self.current_batch.clear()
        self.last_process_time = time.time()
        return None


class ContextAwareAIJudge:
    """上下文感知的AI判断器"""
    
    def __init__(self):
        self.api_ready = False
        self.client = None
        
        # API配置 - 从环境变量读取
        self.api_type = os.getenv("AI_API_TYPE", "openai")
        self.api_key = os.getenv("AI_API_KEY", "")
        self.api_base = os.getenv("AI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("AI_MODEL_NAME", "gpt-4o-mini")
        
        # 验证API配置
        if not self.api_key or self.api_key == "sk-your-api-key-here":
            logger.warning("⚠️ 未配置有效的AI API Key，将使用简化版判断器")
        else:
            logger.info(f"🔑 使用API类型: {self.api_type}, 模型: {self.model_name}")
        
        # 缓存和上下文
        self.template_cache = LRUCache(maxsize=100)
        self.conversation_context = {}
        self.cost_tracker = CostTracker()
        
        # 超时配置
        self.timeout = 30.0
        self.max_retries = 3
        
        # 系统提示
        self.judge_system_prompt = """你是一个专业的弹幕价值判断助手。请判断以下弹幕内容是否有商业价值。

判断标准：
1. 有明确询问商品、服务、价格的 - 高价值
2. 有预约、咨询、挂号需求的 - 高价值  
3. 询问营业时间、地址、联系方式的 - 中价值
4. 有投诉、建议的 - 中价值
5. 表达治疗需求的 - 高价值

无价值内容：
- 纯表情、点赞、闲聊
- 广告、刷屏、灌水
- 与商家业务无关的内容

请返回JSON格式：
{
  "has_value": true/false,
  "content": "提取的关键内容",
  "reason": "判断理由",
  "category": "咨询/预约/询价/投诉/其他",
  "confidence": 0.0-1.0
}"""

        self.reply_system_prompt = """你是一个专业的中医理疗机构客服，需要生成温柔、专业、简洁的回复。

机构特点：
- 专注中医理疗服务
- 提供针灸、推拿、理疗等服务
- 服务态度专业温和

回复要求：
1. 语气温柔、专业、亲切
2. 回复简洁明了，不超过50字
3. 对于具体信息（电话、时间、价格）用"xx"代替
4. 超出知识范围时说："稍等一下，我和老师确认一下，稍后回复您"
5. 体现中医理疗的专业性

请直接返回回复文本，不要包含JSON格式。"""
        
        # 初始化客户端
        asyncio.create_task(self._init_api_client())
    
    async def _init_api_client(self):
        """初始化API客户端"""
        try:
            if self.api_type == "openai":
                await self._init_openai_client()
            else:
                logger.warning(f"不支持的API类型: {self.api_type}")
                return
            
            self.api_ready = True
            logger.info("✅ AI API客户端初始化成功")
            
        except Exception as e:
            logger.error(f"❌ AI API客户端初始化失败: {e}")
            self.api_ready = False
    
    async def _init_openai_client(self):
        """初始化OpenAI客户端"""
        try:
            # 使用httpx作为基础客户端
            self.client = httpx.AsyncClient(
                base_url=self.api_base,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=self.timeout
            )
            logger.info("OpenAI API客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
    
    async def judge_barrages(self, barrages: List[Dict]) -> Optional[AIJudgeResult]:
        """判断弹幕价值（单个处理）"""
        if not self.api_ready or not barrages:
            return None
        
        # 提取有效弹幕
        valid_barrages = [
            b for b in barrages 
            if b.get('type') in ['chat', 'emoji_chat'] and b.get('content', '').strip()
        ]
        
        if not valid_barrages:
            return None
        
        # 构建判断上下文
        context = self._build_judge_context(valid_barrages)
        
        try:
            # 调用AI判断
            response = await self._call_openai_api(
                self.judge_system_prompt, 
                context, 
                response_format="json"
            )
            
            # 解析结果
            result = self._parse_judge_response(response)
            if result and result.has_value:
                logger.info(f"发现有价值弹幕: {result.content}")
                return result
            
        except Exception as e:
            logger.error(f"AI判断失败: {e}")
        
        return None
    
    async def batch_judge_barrages(self, barrages: List[Dict]) -> List[Optional[AIJudgeResult]]:
        """批量判断弹幕价值"""
        if not self.api_ready or not barrages:
            return []
        
        # 分组处理
        results = []
        batch_size = 3  # 每次处理3条弹幕
        
        for i in range(0, len(barrages), batch_size):
            batch = barrages[i:i + batch_size]
            result = await self.judge_barrages(batch)
            results.append(result)
        
        return results
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """生成回复"""
        if not self.api_ready or not content:
            return None
        
        # 检查模板缓存
        cache_key = self._generate_cache_key(content)
        if cached_reply := self.template_cache.get(cache_key):
            logger.info(f"使用缓存回复: {cached_reply}")
            return cached_reply
        
        try:
            # 构建回复上下文
            context = f"顾客问题：{content}\n\n请生成专业回复："
            
            # 调用AI生成回复
            response = await self._call_openai_api(
                self.reply_system_prompt,
                context
            )
            
            # 清理回复
            reply = self._clean_reply(response)
            
            if reply:
                # 缓存常用回复
                self.template_cache.put(cache_key, reply)
                logger.info(f"生成AI回复: {reply}")
                return reply
            
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
        
        return None
    
    async def _call_openai_api(self, system_prompt: str, user_content: str, response_format: str = "text") -> str:
        """调用OpenAI API"""
        if not self.cost_tracker.within_budget():
            raise Exception("超出日成本预算")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # 如果支持JSON模式
        if response_format == "json" and "gpt" in self.model_name.lower():
            data["response_format"] = {"type": "json_object"}
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/chat/completions", json=data)
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # 记录成本
                self.cost_tracker.record_call()
                
                return content
                
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))
        
        return ""
    
    def _build_judge_context(self, barrages: List[Dict]) -> str:
        """构建判断上下文"""
        context_lines = []
        for barrage in barrages:
            content = barrage.get('content', '')
            user = barrage.get('user', 'unknown')
            msg_type = barrage.get('type', 'chat')
            
            context_lines.append(f"【{msg_type}】{user}: {content}")
        
        return "\n".join(context_lines)
    
    def _parse_judge_response(self, response: str) -> Optional[AIJudgeResult]:
        """解析判断响应"""
        try:
            # 清理响应
            response = response.strip()
            
            # 尝试解析JSON
            if response.startswith('{') and response.endswith('}'):
                data = json.loads(response)
            else:
                # 提取JSON部分
                json_match = re.search(r'\{[^{}]*"has_value"[^{}]*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    return None
            
            return AIJudgeResult(
                has_value=data.get('has_value', False),
                content=data.get('content', ''),
                reason=data.get('reason', ''),
                category=data.get('category', 'other'),
                confidence=data.get('confidence', 0.0)
            )
            
        except Exception as e:
            logger.error(f"解析判断响应失败: {e}")
            return None
    
    def _clean_reply(self, response: str) -> str:
        """清理回复文本"""
        if not response:
            return ""
        
        # 移除多余空白
        reply = re.sub(r'\s+', ' ', response).strip()
        
        # 移除可能的JSON包装
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1]
        
        # 移除回复前缀
        reply = re.sub(r'^(回复[:：]?\s*|答[:：]?\s*)', '', reply)
        
        # 限制长度
        if len(reply) > 100:
            reply = reply[:100] + "..."
        
        return reply
    
    def _generate_cache_key(self, content: str) -> str:
        """生成缓存key"""
        # 简化内容用于缓存
        simplified = re.sub(r'[^\w\u4e00-\u9fff]', '', content.lower())
        return hashlib.md5(simplified.encode()).hexdigest()[:8]
    
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.aclose()


class OptimizedAIJudge:
    """优化版AI判断系统"""
    
    def __init__(self):
        self.preprocessor = SmartBarrageProcessor()
        self.ai_judge = ContextAwareAIJudge()
        self.batch_processor = SmartBatchProcessor(self.ai_judge)
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'ignored_count': 0,
            'ai_calls': 0,
            'cache_hits': 0,
            'batch_processed': 0
        }
    
    async def process_barrage_stream(self, barrage: Dict) -> Optional[str]:
        """处理弹幕流"""
        self.stats['total_processed'] += 1
        
        # 预处理
        result = await self.preprocessor.process_barrage(barrage)
        
        if result.action == ProcessAction.IGNORE:
            self.stats['ignored_count'] += 1
            logger.debug(f"忽略弹幕: {result.reason}")
            return None
        
        elif result.action == ProcessAction.PROCESS:
            # 立即处理
            return await self._immediate_process(barrage)
        
        elif result.action == ProcessAction.BATCH:
            # 批处理
            self.stats['batch_processed'] += 1
            return await self.batch_processor.add_to_batch(barrage)
        
        elif result.action == ProcessAction.DEFER:
            # 延迟处理
            await asyncio.sleep(result.delay)
            return await self._immediate_process(barrage)
        
        return None
    
    async def _immediate_process(self, barrage: Dict) -> Optional[str]:
        """立即处理弹幕"""
        try:
            self.stats['ai_calls'] += 1
            
            # AI判断
            ai_result = await self.ai_judge.judge_barrages([barrage])
            
            if ai_result and ai_result.has_value:
                # 生成回复
                reply = await self.ai_judge.generate_reply(ai_result.content)
                return reply
            
        except Exception as e:
            logger.error(f"立即处理失败: {e}")
        
        return None
    
    async def judge_barrages(self, barrages: List[Dict]) -> Optional[Dict]:
        """兼容原接口的判断方法"""
        if not barrages:
            return None
        
        # 使用新的处理流程
        for barrage in barrages:
            result = await self.process_barrage_stream(barrage)
            if result:
                return {
                    'has_value': True,
                    'content': barrage.get('content', ''),
                    'reason': '通过优化流程判断',
                    'category': '咨询'
                }
        
        return None
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """兼容原接口的回复生成方法"""
        return await self.ai_judge.generate_reply(content)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    async def close(self):
        """关闭资源"""
        await self.ai_judge.close()


# 简化版AI判断器（兜底方案）
class SimpleAIJudge:
    """简化版AI判断器"""
    
    def __init__(self):
        self.keyword_filter = KeywordFilter()
        self.api_ready = True
        logger.info("🔄 使用简化版AI判断器")
    
    async def judge_barrages(self, barrages: List[Dict]) -> Optional[Dict]:
        """简化版弹幕判断"""
        try:
            for barrage in barrages:
                content = barrage.get('content', '')
                score = self.keyword_filter.calculate_score(content)
                
                if score > 0.5:
                    return {
                        'has_value': True,
                        'content': content,
                        'reason': '关键词匹配',
                        'category': '咨询'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"简化判断失败: {e}")
            return None
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """简化版回复生成"""
        try:
            if "预约" in content:
                return "您好，预约请联系我们的客服xx，我们会为您安排合适的时间"
            elif "价格" in content or "多少钱" in content:
                return "您好，具体价格请咨询我们的客服xx，我们有多种套餐可选择"
            elif "营业时间" in content:
                return "您好，我们的营业时间是xx点到xx点，具体可咨询客服xx"
            else:
                return "您好，感谢您的咨询，具体信息请联系我们的客服xx"
                
        except Exception as e:
            logger.error(f"简化回复生成失败: {e}")
            return None
    
    async def close(self):
        """关闭资源"""
        pass


# 工厂函数
def create_ai_judge():
    """创建AI判断器实例"""
    try:
        # 检查是否有有效的API配置
        api_key = os.getenv("AI_API_KEY", "")
        if api_key and api_key != "sk-your-api-key-here":
            return OptimizedAIJudge()
        else:
            logger.warning("未配置有效的AI API Key，使用简化版判断器")
            return SimpleAIJudge()
    except Exception as e:
        logger.warning(f"创建优化版AI判断器失败，使用简化版: {e}")
        return SimpleAIJudge()


if __name__ == "__main__":
    # 测试代码
    async def test():
        judge = create_ai_judge()
        
        test_barrages = [
            {"type": "chat", "content": "请问你们的中医理疗多少钱", "user": "test1", "timestamp": time.time()},
            {"type": "chat", "content": "666", "user": "test2", "timestamp": time.time()},
            {"type": "chat", "content": "我想预约针灸", "user": "test3", "timestamp": time.time()},
        ]
        
        for barrage in test_barrages:
            if hasattr(judge, 'process_barrage_stream'):
                result = await judge.process_barrage_stream(barrage)
                print(f"弹幕: {barrage['content']} -> 回复: {result}")
            else:
                result = await judge.judge_barrages([barrage])
                if result and result.get('has_value'):
                    reply = await judge.generate_reply(result.get('content'))
                    print(f"弹幕: {barrage['content']} -> 回复: {reply}")
        
        await judge.close()
    
    asyncio.run(test())
