For thinking mode, use Temperature=0.6, TopP=0.95, TopK=20, and MinP=0 (the default setting in generation_config.json). DO NOT use greedy decoding, as it can lead to performance degradation and endless repetitions. For more detailed guidance, please refer to the Best Practices section.

enable_thinking=False
We provide a hard switch to strictly disable the model's thinking behavior, aligning its functionality with the previous Qwen2.5-Instruct models. This mode is particularly useful in scenarios where disabling thinking is essential for enhancing efficiency.

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False  # Setting enable_thinking=False disables thinking mode
)


For non-thinking mode, we suggest using Temperature=0.7, TopP=0.8, TopK=20, and MinP=0. For more detailed guidance, please refer to the Best Practices section.


Standardize Output Format: We recommend using prompts to standardize model outputs when benchmarking.

Math Problems: Include "Please reason step by step, and put your final answer within \boxed{}." in the prompt.
Multiple-Choice Questions: Add the following JSON structure to the prompt to standardize responses: "Please show your choice in the answer field with only the choice letter, e.g., "answer": "C"."


# 流式输出
import openai

client = openai.OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
stream = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Explain streaming in Qwen3"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
