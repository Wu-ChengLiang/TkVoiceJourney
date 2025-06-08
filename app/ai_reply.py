#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI回复生成器
使用OpenAI流式输出和固定模板回复
"""

import asyncio
import hashlib
import json
import logging
import random
import re
import time
from typing import AsyncIterator, Dict, List, Optional, Tuple
from dataclasses import dataclass

import httpx
from config import (
    OPENAI_CONFIG, 
    TEMPLATE_REPLIES, 
    HIGH_VALUE_KEYWORDS, 
    RESTAURANT_CONFIG
)

logger = logging.getLogger(__name__)


@dataclass
class ReplyResult:
    """回复结果"""
    text: str
    is_template: bool = False
    category: str = "默认"
    confidence: float = 0.0
    generation_time: float = 0.0


class TemplateReplyGenerator:
    """模板回复生成器"""
    
    def __init__(self):
        self.template_cache = {}
        self.usage_stats = {category: 0 for category in TEMPLATE_REPLIES.keys()}
    
    def detect_category(self, content: str) -> str:
        """检测弹幕内容类别"""
        content = content.lower()
        
        # 按优先级检测关键词
        for category, keywords in HIGH_VALUE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    return category
        
        return "默认"
    
    def generate_template_reply(self, content: str, category: str = None) -> ReplyResult:
        """生成模板回复"""
        if not category:
            category = self.detect_category(content)
        
        # 获取该类别的模板
        templates = TEMPLATE_REPLIES.get(category, TEMPLATE_REPLIES["默认"])
        
        # 随机选择一个模板（避免重复）
        self.usage_stats[category] += 1
        template_index = self.usage_stats[category] % len(templates)
        reply_text = templates[template_index]
        
        # 替换占位符
        reply_text = self._replace_placeholders(reply_text, category)
        
        return ReplyResult(
            text=reply_text,
            is_template=True,
            category=category,
            confidence=0.8,
            generation_time=0.01
        )
    
    def _replace_placeholders(self, text: str, category: str) -> str:
        """替换模板中的占位符"""
        replacements = {
            'xx': RESTAURANT_CONFIG['avg_price'],
            '美味餐厅': RESTAURANT_CONFIG['name'],
            'XX餐厅': RESTAURANT_CONFIG['name'],
            'xx菜系': RESTAURANT_CONFIG['cuisine_type'],
            'xx公里': '5',
            'xx站': '市中心',
            'xx平台': '美团/饿了么',
            'xx元起': f"{RESTAURANT_CONFIG['avg_price']}元起"
        }
        
        for placeholder, replacement in replacements.items():
            text = text.replace(placeholder, replacement)
        
        return text


class OpenAIStreamReplyGenerator:
    """OpenAI流式回复生成器"""
    
    def __init__(self):
        self.client = None
        self.api_ready = False
        self._init_client()
        
        # 系统提示
        self.system_prompt = f"""你是【{RESTAURANT_CONFIG['name']}】的抖音小助理，需要生成活泼温暖、专业贴心的回复。

餐厅特色：
- 主打{RESTAURANT_CONFIG['cuisine_type']}
- 提供{'/'.join(RESTAURANT_CONFIG['services'])}服务
- 人均消费约{RESTAURANT_CONFIG['avg_price']}元
- 招牌菜：{', '.join(RESTAURANT_CONFIG['features'])}

回复要求：
1. 语气活泼可爱，用"宝子""亲"等亲切称呼
2. 回复简洁有温度，带emoji，不超过50字
3. 关键信息用"xx"代替（如"人均xx元起~"）
4. 适当使用餐饮话术："爆款菜品""招牌必点"等

示例：
"宝子想订几人位呀？周末建议提前2天预约哦~ 🌸"

请直接返回回复文本，不要包含JSON格式。"""
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            if not OPENAI_CONFIG["api_key"]:
                logger.warning("未配置OpenAI API Key")
                return
            
            self.client = httpx.AsyncClient(
                base_url=OPENAI_CONFIG["api_base"],
                headers={
                    "Authorization": f"Bearer {OPENAI_CONFIG['api_key']}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            self.api_ready = True
            logger.info("✅ OpenAI客户端初始化成功")
            
        except Exception as e:
            logger.error(f"❌ OpenAI客户端初始化失败: {e}")
            self.api_ready = False
    
    async def generate_reply_stream(self, content: str) -> AsyncIterator[str]:
        """生成流式回复"""
        if not self.api_ready:
            yield "稍等哦，小助理马上去通知店家确认~"
            return
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"顾客问题：{content}\n\n请生成专业回复："}
            ]
            
            data = {
                "model": OPENAI_CONFIG["model"],
                "messages": messages,
                "max_tokens": OPENAI_CONFIG["max_tokens"],
                "temperature": OPENAI_CONFIG["temperature"],
                "stream": True
            }
            
            async with self.client.stream("POST", "/chat/completions", json=data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"OpenAI流式生成失败: {e}")
            yield "稍等哦，小助理马上去通知店家确认~"
    
    async def generate_reply(self, content: str) -> ReplyResult:
        """生成完整回复"""
        start_time = time.time()
        reply_parts = []
        
        async for part in self.generate_reply_stream(content):
            reply_parts.append(part)
        
        reply_text = "".join(reply_parts).strip()
        generation_time = time.time() - start_time
        
        # 清理回复
        reply_text = self._clean_reply(reply_text)
        
        return ReplyResult(
            text=reply_text,
            is_template=False,
            category="AI生成",
            confidence=0.9,
            generation_time=generation_time
        )
    
    def _clean_reply(self, text: str) -> str:
        """清理AI生成的回复"""
        if not text:
            return "稍等哦，小助理马上去通知店家确认~"
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除可能的JSON包装
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # 移除回复前缀
        text = re.sub(r'^(回复[:：]?\s*|答[:：]?\s*)', '', text)
        
        # 限制长度
        if len(text) > 100:
            text = text[:100] + "..."
        
        return text
    
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.aclose()


class SmartReplyGenerator:
    """智能回复生成器（模板+AI混合）"""
    
    def __init__(self):
        self.template_generator = TemplateReplyGenerator()
        self.ai_generator = OpenAIStreamReplyGenerator()
        
        # 策略配置
        self.template_threshold = 0.7  # 模板回复阈值
        self.ai_fallback = True  # AI回复兜底
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'template_replies': 0,
            'ai_replies': 0,
            'fallback_replies': 0
        }
    
    async def generate_reply(self, content: str) -> ReplyResult:
        """智能生成回复"""
        self.stats['total_requests'] += 1
        
        try:
            # 1. 尝试模板回复
            category = self.template_generator.detect_category(content)
            
            # 高置信度使用模板回复
            if category != "默认" and self._should_use_template(content, category):
                self.stats['template_replies'] += 1
                return self.template_generator.generate_template_reply(content, category)
            
            # 2. 使用AI生成回复
            if self.ai_generator.api_ready:
                self.stats['ai_replies'] += 1
                return await self.ai_generator.generate_reply(content)
            
            # 3. 兜底使用模板回复
            self.stats['fallback_replies'] += 1
            return self.template_generator.generate_template_reply(content, "默认")
            
        except Exception as e:
            logger.error(f"回复生成失败: {e}")
            self.stats['fallback_replies'] += 1
            return ReplyResult(
                text="稍等哦，小助理马上去通知店家确认~",
                is_template=True,
                category="错误兜底",
                confidence=0.5
            )
    
    async def generate_reply_stream(self, content: str) -> AsyncIterator[str]:
        """生成流式回复"""
        try:
            # 检查是否应该使用模板回复
            category = self.template_generator.detect_category(content)
            
            if category != "默认" and self._should_use_template(content, category):
                # 立即返回模板回复
                template_result = self.template_generator.generate_template_reply(content, category)
                yield template_result.text
                return
            
            # 使用AI流式生成
            if self.ai_generator.api_ready:
                async for part in self.ai_generator.generate_reply_stream(content):
                    yield part
            else:
                # 兜底模板回复
                fallback_result = self.template_generator.generate_template_reply(content, "默认")
                yield fallback_result.text
                
        except Exception as e:
            logger.error(f"流式回复生成失败: {e}")
            yield "稍等哦，小助理马上去通知店家确认~"
    
    def _should_use_template(self, content: str, category: str) -> bool:
        """判断是否应该使用模板回复"""
        # 简单问题优先使用模板
        simple_patterns = [
            r'^.{0,10}(价格|多少钱|费用)',  # 简短的价格询问
            r'^.{0,10}(地址|在哪|位置)',   # 简短的地址询问
            r'^.{0,10}(营业时间|几点)',    # 简短的时间询问
            r'^.{0,8}(预约|订位)',        # 简短的预约
        ]
        
        for pattern in simple_patterns:
            if re.search(pattern, content):
                return True
        
        # 对于复杂问题，使用AI生成
        return len(content) < 15
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats['total_requests']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'template_rate': self.stats['template_replies'] / total,
            'ai_rate': self.stats['ai_replies'] / total,
            'fallback_rate': self.stats['fallback_replies'] / total
        }
    
    async def close(self):
        """关闭资源"""
        await self.ai_generator.close()


# 创建全局实例
def create_reply_generator() -> SmartReplyGenerator:
    """创建回复生成器实例"""
    return SmartReplyGenerator()


if __name__ == "__main__":
    # 测试代码
    async def test():
        generator = create_reply_generator()
        
        test_cases = [
            "价格多少钱",
            "我想预约",
            "你们地址在哪",
            "营业时间几点到几点",
            "推荐什么菜",
            "你们这个川菜正宗吗，我想了解一下特色菜品和用餐环境"
        ]
        
        for content in test_cases:
            print(f"\n问题: {content}")
            
            # 测试普通回复
            result = await generator.generate_reply(content)
            print(f"回复: {result.text}")
            print(f"类型: {'模板' if result.is_template else 'AI'}")
            print(f"类别: {result.category}")
            
            # 测试流式回复
            print("流式: ", end="")
            async for part in generator.generate_reply_stream(content):
                print(part, end="", flush=True)
            print()
        
        print(f"\n统计信息: {generator.get_stats()}")
        await generator.close()
    
    asyncio.run(test())
