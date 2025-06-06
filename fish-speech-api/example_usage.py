"""
Fish Audio TTS 使用示例
"""

from fish_tts_client import FishTTSClient
import os

def main():
    # 初始化客户端（已经包含你的API key）
    client = FishTTSClient()
    
    print("🎵 Fish Audio TTS 测试开始")
    print("=" * 50)
    
    # 测试文本列表
    test_texts = [
        "你好世界！这是Fish Audio的语音合成测试。",
        "Hello, world! This is a Fish Audio TTS test.",
        "今天天气真不错，适合出去走走。",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    # 可用的模型
    models = ["speech-1.5", "speech-1.6", "s1", "s1-mini"]
    
    for i, text in enumerate(test_texts):
        print(f"\n📝 测试 {i+1}: {text}")
        
        # 选择模型（循环使用不同模型）
        model = models[i % len(models)]
        print(f"🔧 使用模型: {model}")
        
        # 输出文件名
        output_file = f"test_output_{i+1}.mp3"
        
        # 调用TTS（优先使用SDK，如果不可用则使用Raw API）
        success = client.tts(
            text=text,
            output_file=output_file,
            use_sdk=True,  # 优先使用SDK
            model=model
        )
        
        if success:
            file_size = os.path.getsize(output_file) / 1024  # KB
            print(f"✅ 成功生成: {output_file} ({file_size:.1f} KB)")
        else:
            print(f"❌ 生成失败")
    
    print("\n" + "=" * 50)
    print("🎵 Fish Audio TTS 测试完成")


def test_with_reference_audio():
    """使用参考音频的测试（如果有参考音频文件）"""
    client = FishTTSClient()
    
    # 检查是否有参考音频文件
    ref_audio_files = ["lengyue.wav", "reference.wav", "sample.wav"]
    ref_audio_path = None
    
    for file in ref_audio_files:
        if os.path.exists(file):
            ref_audio_path = file
            break
    
    if ref_audio_path:
        print(f"\n🎤 使用参考音频测试: {ref_audio_path}")
        
        success = client.tts(
            text="这是使用参考音频克隆声音的测试",
            output_file="test_with_reference.mp3",
            use_sdk=False,  # 使用Raw API支持参考音频
            reference_audio=(ref_audio_path, "参考音频对应的文本"),
            model="speech-1.5"
        )
        
        if success:
            print("✅ 参考音频测试成功")
        else:
            print("❌ 参考音频测试失败")
    else:
        print("\n⚠️  未找到参考音频文件，跳过参考音频测试")


def test_different_formats():
    """测试不同的音频格式"""
    client = FishTTSClient()
    
    print("\n🎵 测试不同音频格式")
    
    formats = [
        ("mp3", 128),
        ("mp3", 192),
        ("wav", None),
    ]
    
    for i, (format_type, bitrate) in enumerate(formats):
        output_file = f"test_format_{format_type}_{bitrate or 'default'}.{format_type}"
        
        kwargs = {
            "text": f"这是{format_type}格式的测试",
            "output_file": output_file,
            "use_sdk": False,  # Raw API支持格式设置
            "format": format_type,
            "model": "speech-1.5"
        }
        
        if format_type == "mp3" and bitrate:
            kwargs["mp3_bitrate"] = bitrate
        
        print(f"🔧 生成格式: {format_type}" + (f" ({bitrate}kbps)" if bitrate else ""))
        
        success = client.tts(**kwargs)
        
        if success:
            file_size = os.path.getsize(output_file) / 1024  # KB
            print(f"✅ 成功: {output_file} ({file_size:.1f} KB)")


if __name__ == "__main__":
    main()
    test_with_reference_audio()
    test_different_formats() 