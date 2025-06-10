#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI回复生成器
使用OpenAI流式输出和固定模板回复（模板功能已注释）
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
    # TEMPLATE_REPLIES,  # 模板回复已注释
    # HIGH_VALUE_KEYWORDS,  # 高价值关键词已注释
    RESTAURANT_CONFIG
)

logger = logging.getLogger(__name__)


@dataclass
class ReplyResult:
    """回复结果"""
    text: str
    is_template: bool = False
    category: str = "AI生成"
    confidence: float = 0.9
    generation_time: float = 0.0


# class TemplateReplyGenerator:
#     """模板回复生成器 - 已注释禁用"""
#     
#     def __init__(self):
#         self.template_cache = {}
#         self.usage_stats = {category: 0 for category in TEMPLATE_REPLIES.keys()}
#     
#     def detect_category(self, content: str) -> str:
#         """检测弹幕内容类别"""
#         content = content.lower()
#         
#         # 按优先级检测关键词
#         for category, keywords in HIGH_VALUE_KEYWORDS.items():
#             for keyword in keywords:
#                 if keyword in content:
#                     return category
#         
#         return "默认"
#     
#     def generate_template_reply(self, content: str, category: str = None) -> ReplyResult:
#         """生成模板回复"""
#         if not category:
#             category = self.detect_category(content)
#         
#         # 获取该类别的模板
#         templates = TEMPLATE_REPLIES.get(category, TEMPLATE_REPLIES["默认"])
#         
#         # 随机选择一个模板（避免重复）
#         self.usage_stats[category] += 1
#         template_index = self.usage_stats[category] % len(templates)
#         reply_text = templates[template_index]
#         
#         # 替换占位符
#         reply_text = self._replace_placeholders(reply_text, category)
#         
#         return ReplyResult(
#             text=reply_text,
#             is_template=True,
#             category=category,
#             confidence=0.8,
#             generation_time=0.01
#         )
#     
#     def _replace_placeholders(self, text: str, category: str) -> str:
#         """替换模板中的占位符"""
#         replacements = {
#             'xx': RESTAURANT_CONFIG['avg_price'],
#             '美味餐厅': RESTAURANT_CONFIG['name'],
#             'XX餐厅': RESTAURANT_CONFIG['name'],
#             'xx菜系': RESTAURANT_CONFIG['cuisine_type'],
#             'xx公里': '5',
#             'xx站': '市中心',
#             'xx平台': '美团/饿了么',
#             'xx元起': f"{RESTAURANT_CONFIG['avg_price']}元起"
#         }
#         
#         for placeholder, replacement in replacements.items():
#             text = text.replace(placeholder, replacement)
#         
#         return text


class OpenAIStreamReplyGenerator:
    """OpenAI流式回复生成器"""
    
    def __init__(self):
        self.client = None
        self.api_ready = False
        self._init_client()
        
        # 系统提示 - 根据最新配置文件更新
        self.system_prompt = f"""你是【{RESTAURANT_CONFIG['name']}】的抖音小助理，需要生成活泼温暖、专业贴心的回复。

餐厅详细信息：
- 名称：{RESTAURANT_CONFIG['name']}
- 类型：{RESTAURANT_CONFIG['cuisine_type']}
- 地址：{RESTAURANT_CONFIG['location']}
- 电话：{RESTAURANT_CONFIG['phone']}
- 营业时间：{RESTAURANT_CONFIG['business_hours']}（{RESTAURANT_CONFIG['status']}）
- 评分：{RESTAURANT_CONFIG['rating']}
- 人均消费：约{RESTAURANT_CONFIG['avg_price']}元
- 服务：{'/'.join(RESTAURANT_CONFIG['services'])}

特色与风格：
{RESTAURANT_CONFIG['style']}

招牌特色：
{', '.join(RESTAURANT_CONFIG['features'])}

特惠套餐：
{RESTAURANT_CONFIG.get('set meal', '')}

回复要求：
1. 语气活泼可爱，用"宝子""亲"等亲切称呼
2. 回复生动有趣，不带emoji，12~30字左右，可以像是俏皮的邻家女孩，
3. 适当提及特色菜品、套餐等亮点

请直接返回回复文本，不要包含JSON格式。

"""
    
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
            yield "稍等哦，小助理马上去通知店家确认~ 🤗"
    
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
        
        # 检测回复类别
        category = self._detect_reply_category(content)
        
        return ReplyResult(
            text=reply_text,
            is_template=False,
            category=category,
            confidence=0.9,
            generation_time=generation_time
        )
    
    def _clean_reply(self, text: str) -> str:
        """清理AI生成的回复"""
        if not text:
            return "稍等哦，小助理马上去通知店家确认~ 🤗"
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除可能的JSON包装
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # 移除回复前缀
        text = re.sub(r'^(回复[:：]?\s*|答[:：]?\s*)', '', text)
        
        # 限制长度
        if len(text) > 120:
            text = text[:120] + "..."
        
        return text
    
    def _detect_reply_category(self, content: str) -> str:
        """检测回复类别"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['预约', '订位', '定位', '订桌']):
            return "预约咨询"
        elif any(word in content_lower for word in ['价格', '多少钱', '消费', '人均', '套餐']):
            return "价格咨询"
        elif any(word in content_lower for word in ['地址', '在哪', '位置', '怎么走']):
            return "地址咨询"
        elif any(word in content_lower for word in ['推荐', '特色', '招牌', '好吃']):
            return "菜品推荐"
        elif any(word in content_lower for word in ['营业时间', '几点', '开门', '关门']):
            return "营业时间"
        elif any(word in content_lower for word in ['电话', '联系', '客服']):
            return "联系方式"
        else:
            return "通用咨询"
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "api_ready": self.api_ready,
            "model": OPENAI_CONFIG["model"],
            "restaurant": RESTAURANT_CONFIG["name"]
        }
    
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.aclose()


class SmartReplyGenerator:
    """智能回复生成器（当前只使用AI，模板功能已注释）"""
    
    def __init__(self):
        # self.template_generator = TemplateReplyGenerator()  # 模板生成器已注释
        self.ai_generator = OpenAIStreamReplyGenerator()
        
        # 策略配置
        # self.template_threshold = 0.7  # 模板回复阈值 - 已注释
        self.ai_fallback = True  # AI回复兜底
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            # 'template_replies': 0,  # 模板回复统计已注释
            'ai_replies': 0,
            'fallback_replies': 0,
            'avg_generation_time': 0.0
        }
    
    async def generate_reply(self, content: str) -> ReplyResult:
        """智能生成回复（当前只使用AI）"""
        self.stats['total_requests'] += 1
        
        try:
            # 模板回复功能已注释，直接使用AI生成
            # # 1. 尝试模板回复
            # category = self.template_generator.detect_category(content)
            # 
            # # 高置信度使用模板回复
            # if category != "默认" and self._should_use_template(content, category):
            #     self.stats['template_replies'] += 1
            #     return self.template_generator.generate_template_reply(content, category)
            
            # 使用AI生成回复
            if self.ai_generator.api_ready:
                self.stats['ai_replies'] += 1
                result = await self.ai_generator.generate_reply(content)
                
                # 更新平均生成时间
                self._update_avg_time(result.generation_time)
                
                return result
            
            # 兜底回复
            self.stats['fallback_replies'] += 1
            return ReplyResult(
                text="稍等哦，小助理马上去通知店家确认~ 🤗",
                is_template=False,
                category="系统兜底",
                confidence=0.5
            )
            
        except Exception as e:
            logger.error(f"回复生成失败: {e}")
            self.stats['fallback_replies'] += 1
            return ReplyResult(
                text="稍等哦，小助理马上去通知店家确认~ 🤗",
                is_template=False,
                category="错误兜底",
                confidence=0.5
            )
    
    async def generate_reply_stream(self, content: str) -> AsyncIterator[str]:
        """生成流式回复（当前只使用AI）"""
        try:
            # 模板回复功能已注释，直接使用AI流式生成
            # # 检查是否应该使用模板回复
            # category = self.template_generator.detect_category(content)
            # 
            # if category != "默认" and self._should_use_template(content, category):
            #     # 立即返回模板回复
            #     template_result = self.template_generator.generate_template_reply(content, category)
            #     yield template_result.text
            #     return
            
            # 使用AI流式生成
            if self.ai_generator.api_ready:
                async for part in self.ai_generator.generate_reply_stream(content):
                    yield part
            else:
                # 兜底回复
                yield "稍等哦，小助理马上去通知店家确认~ 🤗"
                
        except Exception as e:
            logger.error(f"流式回复生成失败: {e}")
            yield "稍等哦，小助理马上去通知店家确认~ 🤗"
    
    # def _should_use_template(self, content: str, category: str) -> bool:
    #     """判断是否应该使用模板回复 - 已注释"""
    #     # 简单问题优先使用模板
    #     simple_patterns = [
    #         r'^.{0,10}(价格|多少钱|费用)',  # 简短的价格询问
    #         r'^.{0,10}(地址|在哪|位置)',   # 简短的地址询问
    #         r'^.{0,10}(营业时间|几点)',    # 简短的时间询问
    #         r'^.{0,8}(预约|订位)',        # 简短的预约
    #     ]
    #     
    #     for pattern in simple_patterns:
    #         if re.search(pattern, content):
    #             return True
    #     
    #     # 对于复杂问题，使用AI生成
    #     return len(content) < 15
    
    def _update_avg_time(self, generation_time: float):
        """更新平均生成时间"""
        if self.stats['ai_replies'] > 1:
            self.stats['avg_generation_time'] = (
                (self.stats['avg_generation_time'] * (self.stats['ai_replies'] - 1) + generation_time) 
                / self.stats['ai_replies']
            )
        else:
            self.stats['avg_generation_time'] = generation_time
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats['total_requests']
        base_stats = {
            **self.stats,
            # 'template_rate': self.stats['template_replies'] / total if total > 0 else 0,  # 已注释
            'ai_rate': self.stats['ai_replies'] / total if total > 0 else 0,
            'fallback_rate': self.stats['fallback_replies'] / total if total > 0 else 0
        }
        
        # 合并AI生成器统计
        ai_stats = self.ai_generator.get_stats()
        return {**base_stats, **ai_stats}
    
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
            "我想预约今晚的位置",
            "你们地址在哪",
            "营业时间几点到几点",
            "推荐什么特色菜",
            "有什么套餐优惠吗",
            "你们这个餐厅怎么样，环境如何"
        ]
        
        print(f"🍽️ 测试 {RESTAURANT_CONFIG['name']} AI回复系统")
        
        for i, content in enumerate(test_cases, 1):
            print(f"\n--- 测试 {i} ---")
            print(f"问题: {content}")
            
            # 测试普通回复
            result = await generator.generate_reply(content)
            print(f"回复: {result.text}")
            print(f"类别: {result.category}")
            print(f"生成时间: {result.generation_time:.2f}s")
            
            # 测试流式回复
            print("流式: ", end="")
            async for part in generator.generate_reply_stream(content):
                print(part, end="", flush=True)
            print()
        
        print(f"\n📊 统计信息: {generator.get_stats()}")
        await generator.close()
    
    asyncio.run(test())
