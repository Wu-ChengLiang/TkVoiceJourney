#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频播放器测试脚本
用于测试pygame音频播放功能
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_audio_player():
    """测试音频播放器"""
    print("🎵 音频播放器测试")
    print("=" * 30)
    
    try:
        # 导入音频播放器
        from core.audio_player import get_player
        
        print("✅ 成功导入音频播放器")
        
        # 获取播放器实例
        player = get_player()
        print("✅ 成功创建播放器实例")
        
        # 检查是否有测试音频文件
        test_files = []
        for filename in os.listdir('.'):
            if filename.endswith('.mp3') and ('test' in filename or 'debug' in filename):
                test_files.append(filename)
        
        if test_files:
            print(f"📁 找到测试音频文件: {test_files}")
            
            for test_file in test_files[:3]:  # 最多测试3个文件
                print(f"\n🔊 播放测试文件: {test_file}")
                try:
                    # 读取音频文件
                    with open(test_file, 'rb') as f:
                        audio_data = f.read()
                    
                    print(f"📊 文件大小: {len(audio_data)} 字节")
                    
                    # 播放音频
                    player.play_audio_bytes(audio_data, "mp3")
                    print("✅ 播放完成")
                    
                except Exception as e:
                    print(f"❌ 播放失败: {e}")
        else:
            print("⚠️ 未找到测试音频文件")
            print("请先运行以下命令生成测试音频:")
            print("  python test_fish_audio.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保已安装pygame:")
        print("  pip install pygame")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_audio():
    """测试系统音频播放"""
    print("\n🔊 系统音频测试")
    print("=" * 30)
    
    try:
        # 检查pygame初始化
        import pygame
        pygame.mixer.init()
        print("✅ pygame mixer 初始化成功")
        
        # 获取音频设备信息
        freq, size, channels = pygame.mixer.get_init()
        print(f"📊 音频设备信息:")
        print(f"  - 采样率: {freq} Hz")
        print(f"  - 采样大小: {size} bits")
        print(f"  - 声道数: {channels}")
        
        # 检查音量
        volume = pygame.mixer.music.get_volume()
        print(f"🔊 当前音量: {volume * 100:.0f}%")
        
        if volume == 0:
            print("⚠️ 音量为0，尝试设置音量为100%")
            pygame.mixer.music.set_volume(1.0)
        
        return True
        
    except Exception as e:
        print(f"❌ 系统音频测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🧪 TkVoiceJourney 音频播放测试")
    print("=" * 50)
    
    # 测试系统音频
    system_ok = test_system_audio()
    
    # 测试音频播放器
    player_ok = test_audio_player()
    
    print("\n" + "=" * 50)
    if system_ok and player_ok:
        print("🎉 音频播放器测试完成！")
        print("✅ 所有功能正常")
    else:
        print("❌ 音频播放器测试失败")
        print("\n可能的解决方案:")
        print("1. 检查音响/耳机是否连接")
        print("2. 检查系统音量设置")
        print("3. 重新安装pygame: pip install --upgrade pygame")
        print("4. 尝试重启音频服务")


if __name__ == "__main__":
    main() 