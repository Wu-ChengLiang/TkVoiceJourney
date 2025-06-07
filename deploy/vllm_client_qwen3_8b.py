#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLLM客户端实现
通过OpenAI兼容的API调用VLLM服务
"""

from openai import OpenAI
import re


class VLLMClient:
    def __init__(self, base_url):
        """
        初始化VLLM客户端
        
        Args:
            base_url (str): VLLM服务的基础URL，例如 "http://localhost:8000/v1"
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key="EMPTY",
        )

    def generate_with_thinking(self, prompt, model="Qwen3"):
        """
        使用vllm生成带thinking的回答
        
        Args:
            prompt (str): 用户输入的提示
            model (str): 模型名称，默认为"Qwen3"
            
        Returns:
            dict: 包含'reasoning'和'answer'的字典
        """
        messages = [
            {"role": "system", "content": "你是一个餐饮抖音客服，按照语气回答"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
            )

            reasoning_content = getattr(response.choices[0].message, 'reasoning_content', '')
            answer_content = response.choices[0].message.content

            # 处理可能为None的情况
            if reasoning_content is None:
                reasoning_content = ''
            if answer_content is None:
                answer_content = ''

            return {
                'reasoning': reasoning_content,
                'answer': answer_content
            }
        except Exception as e:
            print(f"VLLM调用错误: {e}")
            return {
                'reasoning': f'VLLM调用失败: {str(e)}',
                'answer': f'生成失败: {str(e)}'
            }

    def generate_simple(self, prompt, model="Qwen3", remove_thinking=True):
        """
        简单生成方法，可选择是否移除思维链标签
        
        Args:
            prompt (str): 用户输入的提示
            model (str): 模型名称，默认为"Qwen3"
            remove_thinking (bool): 是否移除<think>标签，默认为True
            
        Returns:
            str: 生成的回答内容
        """
        result = self.generate_with_thinking(prompt, model)
        answer = result['answer']
        
        if remove_thinking and answer:
            # 移除<think> </think>之间的内容
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            answer = answer.strip()
            
        return answer

    def test_connection(self):
        """
        测试与VLLM服务的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.generate_simple("测试连接", remove_thinking=True)
            return "生成失败" not in response
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False


def main():
    """
    使用示例
    """
    # 初始化客户端 - 请根据实际情况修改base_url
    base_url = "https://u690372-8e79-a795d08c.cqa1.seetacloud.com:8443/v1"  # 修改为您的VLLM服务地址
    
    client = VLLMClient(base_url)
    
    # 测试连接
    print("测试连接...")
    if client.test_connection():
        print("✓ 连接成功")
    else:
        print("✗ 连接失败，请检查VLLM服务是否正常运行")
        return
    
    # # 示例1: 带思维链的生成
    # print("\n=== 示例1: 带思维链的生成 ===")
    # prompt1 = "你是薇薇的电子宠物，请给她写封情书"
    # result1 = client.generate_with_thinking(prompt1)
    # print(f"推理过程: {result1['reasoning']}")
    # print(f"答案: {result1['answer']}")
    
    # 示例2: 简单生成（移除思维链）
    print("\n=== 示例2: 简单生成（移除思维链） ===")

    # pormpt 是抖音弹幕，
    prompt2 = "你是一个餐饮抖音客服，按照语气回答"
    answer2 = client.generate_simple(prompt2)
    print(f"{answer2}")
    # 把这个输入到tts 接口，然后导出文件存储到文件夹，并且自动清理 自动播放mp3格式文件，并且
    
    # # 示例3: 保留思维链的简单生成
    # print("\n=== 示例3: 保留思维链的简单生成 ===")
    # answer3 = client.generate_simple(prompt2, remove_thinking=False)
    # print(f"答案（含思维链）: {answer3}")


if __name__ == "__main__":
    main() 