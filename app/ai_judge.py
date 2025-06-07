#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI判断模块
基于API进行弹幕价值判断和商家回复生成
"""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class AIJudge:
    """AI弹幕判断和回复生成系统（API版本）"""
    
    def __init__(self):
        self.client = None
        self.api_ready = False
        
        # API配置
        self.api_type = os.getenv("AI_API_TYPE", "openai")  # openai, claude, vllm, local
        self.api_key = os.getenv("AI_API_KEY", "sk-your-api-key-here")
        self.api_base = os.getenv("AI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("AI_MODEL_NAME", "gpt-3.5-turbo")
        
        # 超时和重试配置
        self.timeout = 30.0
        self.max_retries = 3
        
        # 判断价值的系统提示
        self.judge_system_prompt = """角色：用户提问判断助手
使命：判断下面的抖音弹幕，尤其关注聊天msg，其中是否包含值得商家回复的信息
输出格式：JSON格式，包含以下字段：
- has_value: boolean，是否有价值
- content: string，提取的关键内容
- reason: string，判断理由
- category: string，问题类别（如：咨询、预约、询价等）

判断标准：
1. 有明确询问商品、服务、价格的
2. 有预约、咨询需求的
3. 有投诉、建议的
4. 其他需要商家回应的有价值信息

无价值内容：
1. 纯表情、点赞
2. 无意义聊天
3. 广告、刷屏
4. 与商家业务无关的内容"""

        # 商家回复的系统提示
        self.reply_system_prompt = """角色：名医堂美食商家的女主播客服
使命：根据顾客问题，生成专业、温柔、简洁的回复

品牌信息：
- 名医堂：传承中医文化，服务百姓健康
- 专注医养结合的中医理疗服务
- 优质中医走进社区，解决疼痛、亚健康及脏腑调理

回复要求：
1. 语气温柔、专业、简短
2. 不使用感叹号
3. 超出知识范围时回复：稍等一下，我和老师确认一下，稍后回复您
4. 具体信息用xx代替（如电话、姓名、时间、地点）
5. 体现中医理疗专业性

输出格式：纯文本回复，不包含JSON格式"""
        
        # 异步初始化API客户端
        asyncio.create_task(self._init_api_client())
    
    async def _init_api_client(self):
        """初始化API客户端"""
        try:
            logger.info(f"🤖 初始化AI API客户端 (类型: {self.api_type})")
            
            if self.api_type == "openai":
                await self._init_openai_client()
            elif self.api_type == "vllm":
                await self._init_vllm_client()
            elif self.api_type == "local":
                await self._init_local_client()
            else:
                logger.warning(f"不支持的API类型: {self.api_type}，使用默认实现")
                await self._init_default_client()
            
            self.api_ready = True
            logger.info("✅ AI API客户端初始化成功")
            
        except Exception as e:
            logger.error(f"❌ AI API客户端初始化失败: {e}")
            self.api_ready = False
    
    async def _init_openai_client(self):
        """初始化OpenAI API客户端"""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base if self.api_base != "https://api.openai.com/v1" else None,
                timeout=self.timeout
            )
            logger.info("OpenAI API客户端初始化成功")
        except ImportError:
            logger.error("缺少openai包，请运行: pip install openai")
            raise
    
    async def _init_vllm_client(self):
        """初始化vLLM API客户端"""
        # vLLM通常使用OpenAI兼容的API
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key or "vllm",
                base_url=self.api_base,
                timeout=self.timeout
            )
            logger.info("vLLM API客户端初始化成功")
        except ImportError:
            logger.error("缺少openai包，请运行: pip install openai")
            raise
    
    async def _init_local_client(self):
        """初始化本地API客户端"""
        # 使用httpx直接调用本地API
        self.client = httpx.AsyncClient(timeout=self.timeout)
        logger.info("本地API客户端初始化成功")
    
    async def _init_default_client(self):
        """初始化默认客户端（模拟API）"""
        self.client = None
        logger.info("使用默认模拟客户端")
    
    async def judge_barrages(self, barrages: List[Dict]) -> Optional[Dict]:
        """判断弹幕是否有价值"""
        if not self.api_ready or not barrages:
            return None
        
        try:
            # 提取聊天消息
            chat_messages = [
                b for b in barrages 
                if b.get('type') in ['chat', 'emoji_chat'] and b.get('content', '').strip()
            ]
            
            if not chat_messages:
                return None
            
            # 构建弹幕文本
            barrage_text = "\n".join([
                f"【{msg.get('raw_type', '聊天msg')}】{msg.get('user', '')}: {msg.get('content', '')}"
                for msg in chat_messages
            ])
            
            # 构建判断prompt
            prompt = f"{self.judge_system_prompt}\n\n弹幕内容：\n{barrage_text}\n\n请判断："
            
            # API推理
            response = await self._call_api(prompt, response_format="json")
            
            # 解析JSON响应
            result = self._parse_judge_response(response)
            
            if result and result.get('has_value'):
                logger.info(f"发现有价值弹幕: {result.get('content')}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"弹幕判断失败: {e}")
            return None
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """生成商家回复"""
        if not self.api_ready or not content:
            return None
        
        try:
            # 构建回复prompt
            prompt = f"{self.reply_system_prompt}\n\n顾客问题：{content}\n\n请回复："
            
            # API推理
            response = await self._call_api(prompt)
            
            # 清理回复文本
            reply = self._clean_reply(response)
            
            if reply:
                logger.info(f"生成AI回复: {reply}")
                return reply
            
            return None
            
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            return None
    
    async def _call_api(self, prompt: str, response_format: str = "text") -> str:
        """调用AI API"""
        if not self.client:
            return await self._mock_api_call(prompt, response_format)
        
        for attempt in range(self.max_retries):
            try:
                if self.api_type in ["openai", "vllm"]:
                    return await self._call_openai_api(prompt, response_format)
                elif self.api_type == "local":
                    return await self._call_local_api(prompt, response_format)
                else:
                    return await self._mock_api_call(prompt, response_format)
                    
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # 指数退避
        
        return ""
    
    async def _call_openai_api(self, prompt: str, response_format: str = "text") -> str:
        """调用OpenAI兼容API"""
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            # 如果支持JSON模式
            if response_format == "json" and "gpt" in self.model_name.lower():
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def _call_local_api(self, prompt: str, response_format: str = "text") -> str:
        """调用本地API"""
        try:
            data = {
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.7,
                "stop": None
            }
            
            response = await self.client.post(
                f"{self.api_base}/generate",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("text", "").strip()
            
        except Exception as e:
            logger.error(f"本地API调用失败: {e}")
            raise
    
    async def _mock_api_call(self, prompt: str, response_format: str = "text") -> str:
        """模拟API调用（用于测试）"""
        logger.info("使用模拟API响应")
        
        if "判断" in prompt and response_format == "json":
            # 模拟判断结果
            if any(keyword in prompt for keyword in ["预约", "咨询", "价格", "多少钱", "营业时间"]):
                return json.dumps({
                    "has_value": True,
                    "content": "客户咨询相关服务信息",
                    "reason": "包含明确的咨询或询价需求",
                    "category": "咨询"
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "has_value": False,
                    "content": "",
                    "reason": "无实质性商业价值",
                    "category": "闲聊"
                }, ensure_ascii=False)
        else:
            # 模拟回复生成
            return "您好，感谢您的咨询。我们名医堂专注中医理疗服务，具体信息请联系我们的客服xx，营业时间是xx点到xx点"
    
    def _parse_judge_response(self, response: str) -> Optional[Dict]:
        """解析判断响应的JSON"""
        try:
            # 清理响应文本
            response = response.strip()
            
            # 尝试直接解析JSON
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            
            # 提取JSON部分
            json_match = re.search(r'\{[^{}]*"has_value"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # 解析失败，返回默认格式
            return {
                "has_value": False,
                "content": "",
                "reason": "响应格式解析失败",
                "category": "unknown"
            }
            
        except Exception as e:
            logger.error(f"解析判断响应失败: {e}")
            return None
    
    def _clean_reply(self, response: str) -> str:
        """清理回复文本"""
        if not response:
            return ""
        
        # 移除多余的空白字符
        reply = re.sub(r'\s+', ' ', response).strip()
        
        # 移除可能的JSON格式包装
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1]
        
        # 移除可能的回复前缀
        reply = re.sub(r'^(回复[:：]?\s*|答[:：]?\s*)', '', reply)
        
        # 限制长度
        if len(reply) > 200:
            reply = reply[:200] + "..."
        
        return reply
    
    async def close(self):
        """关闭API客户端"""
        if hasattr(self.client, 'aclose'):
            await self.client.aclose()


# 简化版AI判断器（API不可用时的兜底方案）
class SimpleAIJudge:
    """简化版AI判断器"""
    
    def __init__(self):
        self.api_ready = True
        logger.info("🔄 使用简化版AI判断器")
    
    async def judge_barrages(self, barrages: List[Dict]) -> Optional[Dict]:
        """简化版弹幕判断"""
        try:
            # 提取聊天消息
            chat_messages = [
                b for b in barrages 
                if b.get('type') in ['chat', 'emoji_chat'] and b.get('content', '').strip()
            ]
            
            if not chat_messages:
                return None
            
            # 简单关键词匹配
            keywords = ["预约", "咨询", "价格", "多少钱", "营业时间", "怎么", "可以", "需要", "想要"]
            
            for msg in chat_messages:
                content = msg.get('content', '')
                if any(keyword in content for keyword in keywords):
                    return {
                        "has_value": True,
                        "content": content,
                        "reason": "包含咨询关键词",
                        "category": "咨询"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"简化判断失败: {e}")
            return None
    
    async def generate_reply(self, content: str) -> Optional[str]:
        """简化版回复生成"""
        try:
            # 根据关键词生成模板回复
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


# 工厂函数：根据配置创建合适的AI判断器
def create_ai_judge() -> AIJudge:
    """创建AI判断器实例"""
    try:
        return AIJudge()
    except Exception as e:
        logger.warning(f"创建AI判断器失败，使用简化版: {e}")
        return SimpleAIJudge() 