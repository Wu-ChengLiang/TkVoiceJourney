#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI回复生成器 - 纯OpenAI流式回复版本
专为Madoka鸠隐日式居酒屋定制
"""

import asyncio
import json
import logging
import re
import time
from typing import AsyncIterator, Optional
from dataclasses import dataclass

import httpx
from config import OPENAI_CONFIG, RESTAURANT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ReplyResult:
    """回复结果"""
    text: str
    category: str = "AI生成"
    confidence: float = 0.9
    generation_time: float = 0.0


class OpenAIStreamReplyGenerator:
    """OpenAI流式回复生成器 - Madoka鸠隐专用"""
    
    def __init__(self):
        self.client = None
        self.api_ready = False
        self._init_client()
        
        # 系统提示 - 针对Madoka鸠隐定制
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

回复要求：
1. 语气活泼可爱，用"宝子""亲"等亲切称呼
2. 回复简洁有温度，带emoji，不超过80字
3. 体现日式居酒屋的氛围感和专业性
4. 适当提及创意料理、鸡尾酒等特色
5. 根据问题类型给出精准回答：
   - 预约：询问人数时间，提醒热门时段需提前
   - 价格：提及人均消费和性价比
   - 地址：准确提供地址和交通信息
   - 推荐：重点推荐鹅肝寿司、创意鸡尾酒等特色
   - 营业时间：11:00-00:00，当前营业中
   - 风格：强调日式居酒屋与西式酒吧的融合

示例：
"宝子想订几人位呀？我们家的鹅肝寿司配鸡尾酒超赞的~ 🍣🍸"

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
            yield "稍等哦，小助理马上去通知店家确认"
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
            yield "稍等哦，小助理马上去通知店家确认"
    
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
            category=category,
            confidence=0.9,
            generation_time=generation_time
        )
    
    def _clean_reply(self, text: str) -> str:
        """清理AI生成的回复"""
        if not text:
            return "稍等哦，小助理马上去通知店家确认"
        
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
        elif any(word in content_lower for word in ['价格', '多少钱', '消费', '人均']):
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


class MadokaReplyGenerator:
    """Madoka鸠隐专用回复生成器"""
    
    def __init__(self):
        self.ai_generator = OpenAIStreamReplyGenerator()
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'ai_replies': 0,
            'fallback_replies': 0,
            'avg_generation_time': 0.0
        }
    
    async def generate_reply(self, content: str) -> ReplyResult:
        """生成回复"""
        self.stats['total_requests'] += 1
        
        try:
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
                text="稍等哦，小助理马上去通知店家确认",
                category="系统兜底",
                confidence=0.5
            )
            
        except Exception as e:
            logger.error(f"回复生成失败: {e}")
            self.stats['fallback_replies'] += 1
            return ReplyResult(
                text="稍等哦，小助理马上去通知店家确认",
                category="错误兜底",
                confidence=0.5
            )
    
    async def generate_reply_stream(self, content: str) -> AsyncIterator[str]:
        """生成流式回复"""
        try:
            # 直接使用AI流式生成
            if self.ai_generator.api_ready:
                async for part in self.ai_generator.generate_reply_stream(content):
                    yield part
            else:
                # 兜底回复
                yield "稍等哦，小助理马上去通知店家确认"
                
        except Exception as e:
            logger.error(f"流式回复生成失败: {e}")
            yield "稍等哦，小助理马上去通知店家确认"
    
    def _update_avg_time(self, generation_time: float):
        """更新平均生成时间"""
        if self.stats['ai_replies'] > 1:
            self.stats['avg_generation_time'] = (
                (self.stats['avg_generation_time'] * (self.stats['ai_replies'] - 1) + generation_time) 
                / self.stats['ai_replies']
            )
        else:
            self.stats['avg_generation_time'] = generation_time
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = self.stats['total_requests']
        base_stats = {
            **self.stats,
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
def create_reply_generator() -> MadokaReplyGenerator:
    """创建回复生成器实例"""
    return MadokaReplyGenerator()


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
            "有什么好的鸡尾酒推荐吗",
            "鹅肝寿司怎么样",
            "你们这个日式居酒屋怎么样，环境如何"
        ]
        
        print(f"🍣 测试 {RESTAURANT_CONFIG['name']} AI回复系统")
        
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
