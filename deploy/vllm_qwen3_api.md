https://u690372-8e79-a795d08c.cqa1.seetacloud.com:8443
可以通过调用openai api的方式调这个


class VLLMClient:
    def __init__(self, base_url):
        """初始化VLLM客户端"""
        self.client = OpenAI(
            base_url=base_url,
            api_key="EMPTY",
        )

    def generate_without_thinking(self, prompt, model="Qwen3"):
        """使用vllm生成不带thinking的回答"""
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