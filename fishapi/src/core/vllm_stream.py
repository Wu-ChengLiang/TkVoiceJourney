#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一LLM流式客户端
支持OpenAI和VLLM的无缝切换
"""

from openai import OpenAI
import asyncio
from typing import AsyncGenerator
import sys
import os

# 添加上级目录到路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    LLM_MODE, 
    OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL,
    VLLM_BASE_URL, VLLM_API_KEY, VLLM_MODEL,
    DEBUG
)


class UnifiedLLMClient:
    """
    统一LLM流式客户端 (支持OpenAI和VLLM切换)
    """
    def __init__(self):
        """初始化统一LLM流式客户端"""
        self.mode = LLM_MODE
        
        if self.mode == "openai":
            # 使用OpenAI配置
            self.client = OpenAI(
                base_url=OPENAI_BASE_URL,
                api_key=OPENAI_API_KEY,
            )
            self.model = OPENAI_MODEL
            if DEBUG:
                print(f"🔄 使用OpenAI模式: {self.model}")
                print(f"🌐 Base URL: {OPENAI_BASE_URL}")
                
        elif self.mode == "vllm":
            # 使用VLLM配置
            if not VLLM_BASE_URL:
                raise ValueError("VLLM Base URL 未配置，请在.env文件中设置 VLLM_BASE_URL")
                
            self.client = OpenAI(
                base_url=VLLM_BASE_URL,
                api_key=VLLM_API_KEY,
            )
            self.model = VLLM_MODEL
            if DEBUG:
                print(f"🔄 使用VLLM模式: {self.model}")
                print(f"🌐 Base URL: {VLLM_BASE_URL}")
        else:
            raise ValueError(f"不支持的LLM模式: {self.mode}，请设置为 'openai' 或 'vllm'")

    async def stream_chat(self, user_input: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        """
        流式聊天生成
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词，可选
            
        Yields:
            str: 流式生成的文本块
        """
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # 默认系统提示词
            messages.append({
                "role": "system", 
                "content": "你是一个智能助手，用简洁明了的语言回答问题。"
            })
        
        messages.append({"role": "user", "content": user_input})

        try:
            # 创建流式响应
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=True,
                max_tokens=1000,
            )

            # 流式返回文本
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
                    
        except Exception as e:
            error_msg = f"LLM API 错误: {str(e)}"
            if DEBUG:
                print(f"❌ {error_msg}")
            yield error_msg

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "测试连接"}],
                max_tokens=10
            )
            print(f"✅ {self.mode.upper()} 连接测试成功")
            return True
        except Exception as e:
            print(f"❌ {self.mode.upper()} 连接测试失败: {e}")
            return False

    def get_models(self) -> list:
        """获取可用模型列表"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            if DEBUG:
                print(f"❌ 获取模型列表失败: {e}")
            return []

    async def simple_chat(self, user_input: str, system_prompt: str = None) -> str:
        """
        简单聊天（非流式）
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词，可选
            
        Returns:
            str: 完整回复
        """
        response = ""
        async for chunk in self.stream_chat(user_input, system_prompt):
            response += chunk
        return response


# 向后兼容的别名
VLLMStreamClient = UnifiedLLMClient


async def main():
    """测试用例"""
    print(f"🧪 测试 {LLM_MODE.upper()} 流式客户端...")
    
    try:
        client = UnifiedLLMClient()
        
        # 测试连接
        if not client.test_connection():
            print("❌ 连接失败，请检查配置")
            return
        
        # 测试获取模型列表
        if DEBUG:
            models = client.get_models()
            if models:
                print(f"📋 可用模型: {models[:5]}...")  # 显示前5个
        
        # 测试流式生成
        print("\n🔄 测试流式生成:")
        print("助手: ", end="", flush=True)
        
        async for chunk in client.stream_chat("你好，请简单介绍一下自己"):
            print(chunk, end='', flush=True)
        
        print("\n\n✅ 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 