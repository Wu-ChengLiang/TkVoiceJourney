#!/usr/bin/env python3
"""
4.2阶段：创建清洁的训练数据集
使用方案C - 最简化格式，避免所有对话格式污染
"""

import json
from pathlib import Path
import re

def clean_and_validate_data():
    """清洁和验证训练数据"""
    
    print("🧹 开始创建清洁训练数据集 - 方案C")
    print("🎯 目标：移除所有格式污染，使用最简化query-response格式")
    print("=" * 60)
    
    # 读取原始数据
    original_data_path = Path("../data/output/train_data.json")
    
    if not original_data_path.exists():
        print(f"❌ 原始数据文件不存在: {original_data_path}")
        return None
        
    with open(original_data_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"📊 原始数据: {len(original_data)}条")
    
    # 定义需要清理的污染关键词
    pollution_keywords = [
        '请根据美团开店宝的相关知识回答用户的问题。',
        '请根据',
        '根据以下信息',
        '请回答',
        '根据上下文'
    ]
    
    # 创建清洁数据集
    clean_data = []
    skipped_count = 0
    
    for i, item in enumerate(original_data):
        try:
            # 提取纯净的问题和回答
            question = item['input'].strip()
            answer = item['output'].strip()
            
            # 数据质量检查
            if not question or not answer:
                print(f"⚠️  跳过空数据: 索引 {i}")
                skipped_count += 1
                continue
                
            if len(question) < 3 or len(answer) < 10:
                print(f"⚠️  跳过过短数据: 索引 {i}")
                skipped_count += 1
                continue
            
            # 清理问题和回答中的格式污染
            for keyword in pollution_keywords:
                question = question.replace(keyword, '').strip()
                answer = answer.replace(keyword, '').strip()
            
            # 清理多余空白和换行
            question = re.sub(r'\s+', ' ', question).strip()
            answer = re.sub(r'\s+', ' ', answer).strip()
            
            # 再次检查清理后的内容
            if not question or not answer:
                print(f"⚠️  清理后为空，跳过: 索引 {i}")
                skipped_count += 1
                continue
            
            # 确保问题以合适的标点结尾
            if not question.endswith(('？', '?', '。', '.', '：', ':')):
                if any(word in question for word in ['什么', '如何', '怎么', '哪些', '能否', '是否']):
                    if not question.endswith('？'):
                        question += '？'
            
            # 创建方案C格式：最简化query-response
            clean_item = {
                "query": question,
                "response": answer
            }
            
            clean_data.append(clean_item)
            
        except Exception as e:
            print(f"❌ 处理数据 {i} 时出错: {e}")
            skipped_count += 1
            continue
    
    print(f"✅ 数据清洁完成:")
    print(f"  📥 原始数据: {len(original_data)}条")
    print(f"  📤 清洁数据: {len(clean_data)}条")
    print(f"  🗑️  跳过数据: {skipped_count}条")
    print()
    
    # 显示清洁前后对比
    if clean_data:
        print("🔍 清洁前后对比示例:")
        print("--- 原始格式 ---")
        orig_sample = original_data[0]
        print(f"instruction: '{orig_sample['instruction']}'")
        print(f"input: '{orig_sample['input']}'")
        print(f"output: '{orig_sample['output']}'")
        print()
        print("--- 清洁后格式 (方案C) ---")
        clean_sample = clean_data[0]
        print(f"query: '{clean_sample['query']}'")
        print(f"response: '{clean_sample['response']}'")
        print()
    
    return clean_data

def save_clean_dataset(clean_data, format_name="clean"):
    """保存清洁数据集"""
    
    if not clean_data:
        print("❌ 没有清洁数据可保存")
        return None
    
    # 创建输出目录
    output_dir = Path("./data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存清洁数据集
    clean_path = output_dir / f"{format_name}_train.json"
    
    with open(clean_path, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 清洁数据集已保存: {clean_path.absolute()}")
    print(f"📦 文件大小: {clean_path.stat().st_size / 1024:.2f} KB")
    
    return clean_path

def validate_clean_dataset(clean_path):
    """验证清洁数据集质量"""
    
    print("\n🔍 验证清洁数据集质量...")
    
    with open(clean_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = []
    
    # 检查格式一致性
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            issues.append(f"索引 {i}: 不是字典格式")
            continue
            
        if 'query' not in item or 'response' not in item:
            issues.append(f"索引 {i}: 缺少必要字段")
            continue
            
        if len(item) != 2:
            issues.append(f"索引 {i}: 包含额外字段: {list(item.keys())}")
            
        # 检查内容质量
        query = item['query']
        response = item['response']
        
        if not query or not response:
            issues.append(f"索引 {i}: 包含空内容")
            
        # 检查是否还有格式污染痕迹
        pollution_keywords = [
            '请根据', '美团开店宝的相关知识', 'Human:', '<|im_start|>', 
            '<|im_end|>', '根据以下信息', '请回答', '根据上下文'
        ]
        
        for keyword in pollution_keywords:
            if keyword in query or keyword in response:
                issues.append(f"索引 {i}: 可能的格式污染 '{keyword}'")
    
    # 统计信息
    avg_query_len = sum(len(item['query']) for item in data) / len(data)
    avg_response_len = sum(len(item['response']) for item in data) / len(data)
    
    print(f"📊 数据集统计:")
    print(f"  总数量: {len(data)}条")
    print(f"  平均问题长度: {avg_query_len:.1f}字符")
    print(f"  平均回答长度: {avg_response_len:.1f}字符")
    print(f"  发现问题: {len(issues)}个")
    
    if issues:
        print("\n⚠️  发现的问题:")
        for issue in issues[:10]:  # 只显示前10个
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 个问题")
    else:
        print("✅ 数据集质量检查通过！")
    
    return len(issues) == 0

def create_sample_preview(clean_path):
    """创建样本预览"""
    
    print("\n📝 数据样本预览:")
    
    with open(clean_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 显示前3个样本
    for i, item in enumerate(data[:3]):
        print(f"\n--- 样本 {i+1} ---")
        print(f"Query: {item['query']}")
        print(f"Response: {item['response']}")
    
    print(f"\n... 共 {len(data)} 条数据")

def main():
    """主函数"""
    
    print("🚀 执行阶段4.2：创建清洁的训练数据集")
    print("💡 采用方案C：最简化query-response格式")
    print("🎯 目标：完全消除格式污染，提升模型质量")
    print("=" * 60)
    
    # 步骤1：清洁数据
    clean_data = clean_and_validate_data()
    if not clean_data:
        print("❌ 数据清洁失败")
        return 1
    
    # 步骤2：保存清洁数据集
    clean_path = save_clean_dataset(clean_data, "clean")
    if not clean_path:
        print("❌ 保存清洁数据集失败")
        return 1
    
    # 步骤3：验证数据质量
    is_valid = validate_clean_dataset(clean_path)
    
    # 步骤4：创建预览
    create_sample_preview(clean_path)
    
    # 总结
    print("\n" + "=" * 60)
    if is_valid:
        print("🎉 阶段4.2完成！清洁数据集创建成功")
        print(f"📁 清洁数据路径: {clean_path.absolute()}")
        print("\n✅ 主要改进:")
        print("  - 移除了所有instruction前缀污染")
        print("  - 使用最简化query-response格式")
        print("  - 避免了conversations对话标记")
        print("  - 清理了多余的空白和格式")
        print("  - 修复了response中的格式污染")
        print("\n🎯 下一步：执行4.3优化提示词模板设计")
    else:
        print("⚠️  阶段4.2完成，但发现数据质量问题")
        print("建议检查并修复问题后再继续")
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    exit(code=main()) 