#!/usr/bin/env python3
"""
TkVoiceJourney 模型性能测试
测试显存使用、推理速度和输出质量
"""

import sys
import time
import torch
import gc
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "deploy"))

from config import get_config
from chat import OptimizedChatModel

class ModelPerformanceTester:
    """模型性能测试器"""
    
    def __init__(self):
        self.config = get_config()
        self.test_questions = [
            "在吗？想预约下午3点",
            "方便停车吗？",
            "有女老师吗？",
            "你们营业到几点？",
            "可以加微信吗？",
            "价格怎么样？",
            "地址在哪里？",
            "需要提前预约吗？"
        ]
        
    def test_memory_usage(self, model: OptimizedChatModel) -> dict:
        """测试显存使用情况"""
        print("\n🔍 显存使用测试")
        print("-" * 30)
        
        results = {}
        
        if not torch.cuda.is_available():
            print("❌ 未检测到CUDA")
            return results
            
        # 清理显存
        model.clear_memory()
        
        # 获取基准显存
        baseline_memory = torch.cuda.memory_allocated() / (1024**3)
        
        # 测试加载后的显存
        if model.model is not None:
            loaded_memory = torch.cuda.memory_allocated() / (1024**3)
            model_memory = loaded_memory - baseline_memory
        else:
            model_memory = 0
            
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        results = {
            "baseline_memory_gb": baseline_memory,
            "model_memory_gb": model_memory,
            "total_memory_gb": total_memory,
            "memory_utilization": (loaded_memory / total_memory) * 100
        }
        
        print(f"📊 基准显存: {baseline_memory:.2f}GB")
        print(f"📊 模型显存: {model_memory:.2f}GB")
        print(f"📊 总显存: {total_memory:.1f}GB")
        print(f"📊 利用率: {results['memory_utilization']:.1f}%")
        
        # 判断显存使用是否合理
        if results['memory_utilization'] < 90:
            print("✅ 显存使用正常")
        else:
            print("⚠️  显存使用接近极限")
            
        return results
    
    def test_inference_speed(self, model: OptimizedChatModel) -> dict:
        """测试推理速度"""
        print("\n⚡ 推理速度测试")
        print("-" * 30)
        
        if model.model is None:
            print("❌ 模型未加载")
            return {}
            
        times = []
        
        for i, question in enumerate(self.test_questions[:5], 1):
            print(f"🧪 测试 {i}/5: {question}")
            
            start_time = time.time()
            response = model.generate_response(question)
            end_time = time.time()
            
            response_time = end_time - start_time
            times.append(response_time)
            
            print(f"⏱️  耗时: {response_time:.2f}s")
            print(f"💬 回复: {response[:50]}{'...' if len(response) > 50 else ''}")
            print()
        
        results = {
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "times": times
        }
        
        print(f"📈 平均响应时间: {results['average_time']:.2f}s")
        print(f"📈 最快响应: {results['min_time']:.2f}s")
        print(f"📈 最慢响应: {results['max_time']:.2f}s")
        
        return results
    
    def test_output_quality(self, model: OptimizedChatModel) -> dict:
        """测试输出质量（思维链过滤等）"""
        print("\n🎯 输出质量测试")
        print("-" * 30)
        
        if model.model is None:
            print("❌ 模型未加载")
            return {}
        
        quality_checks = {
            "has_thinking_chains": 0,
            "has_user_repetition": 0,
            "empty_responses": 0,
            "appropriate_responses": 0
        }
        
        for i, question in enumerate(self.test_questions, 1):
            print(f"🧪 质量检查 {i}/{len(self.test_questions)}: {question}")
            
            response = model.generate_response(question)
            
            # 检查思维链泄露
            thinking_patterns = ['<think>', '</think>', '<思考>', '</思考>', '[思考]', '[想法]']
            if any(pattern in response for pattern in thinking_patterns):
                quality_checks["has_thinking_chains"] += 1
                print("❌ 发现思维链泄露")
            
            # 检查用户输入重复
            if 'user:' in response.lower():
                quality_checks["has_user_repetition"] += 1
                print("❌ 发现用户输入重复")
            
            # 检查空回复
            if len(response.strip()) < 2:
                quality_checks["empty_responses"] += 1
                print("❌ 回复过短或为空")
            
            # 检查回复适当性
            if (len(response) >= 2 and 
                not any(pattern in response for pattern in thinking_patterns) and
                'user:' not in response.lower()):
                quality_checks["appropriate_responses"] += 1
                print("✅ 回复质量良好")
            
            print(f"💬 回复: {response}")
            print()
        
        total_tests = len(self.test_questions)
        quality_score = (quality_checks["appropriate_responses"] / total_tests) * 100
        
        print(f"📊 质量评分: {quality_score:.1f}%")
        print(f"📊 适当回复: {quality_checks['appropriate_responses']}/{total_tests}")
        print(f"📊 思维链泄露: {quality_checks['has_thinking_chains']}")
        print(f"📊 用户输入重复: {quality_checks['has_user_repetition']}")
        print(f"📊 空回复: {quality_checks['empty_responses']}")
        
        return {
            **quality_checks,
            "total_tests": total_tests,
            "quality_score": quality_score
        }
    
    def run_full_test(self, model_name: str = None, quantization: str = None):
        """运行完整测试"""
        print("🧪 TkVoiceJourney 模型性能测试")
        print("=" * 50)
        
        # 创建模型实例
        chat_model = OptimizedChatModel(model_name, quantization)
        
        # 测试模型加载
        print("🚀 加载模型...")
        if not chat_model.setup_model():
            print("❌ 模型加载失败，测试终止")
            return
        
        print("✅ 模型加载成功")
        
        # 运行各项测试
        memory_results = self.test_memory_usage(chat_model)
        speed_results = self.test_inference_speed(chat_model)
        quality_results = self.test_output_quality(chat_model)
        
        # 汇总测试结果
        print("\n📋 测试结果汇总")
        print("=" * 50)
        
        print(f"📦 测试模型: {chat_model.model_name}")
        print(f"⚡ 量化配置: {chat_model.quantization}")
        
        if memory_results:
            print(f"💾 显存使用: {memory_results['model_memory_gb']:.2f}GB ({memory_results['memory_utilization']:.1f}%)")
        
        if speed_results:
            print(f"⏱️  平均响应: {speed_results['average_time']:.2f}s")
        
        if quality_results:
            print(f"🎯 质量评分: {quality_results['quality_score']:.1f}%")
        
        # 清理资源
        chat_model.clear_memory()
        print("\n🧹 测试完成，资源已清理")
        
        return {
            "memory": memory_results,
            "speed": speed_results,
            "quality": quality_results
        }

def main():
    """主函数"""
    tester = ModelPerformanceTester()
    
    # 可以指定要测试的配置
    model_name = None  # 使用默认模型
    quantization = None  # 使用默认量化
    
    # 运行测试
    results = tester.run_full_test(model_name, quantization)
    
    return results

if __name__ == "__main__":
    main() 