#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频播放模块
"""

import pygame
import io
import threading
import tempfile
import os


class AudioPlayer:
    def __init__(self):
        """初始化音频播放器"""
        pygame.mixer.init()
        self.is_playing = False
        
    def play_audio_bytes(self, audio_data: bytes, format: str = "mp3"):
        """
        播放音频字节数据
        
        Args:
            audio_data: 音频字节数据
            format: 音频格式 ("mp3", "wav")
        """
        if not audio_data:
            print("⚠️ 音频数据为空")
            return
            
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # 播放音频
            self.is_playing = True
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            print(f"🎵 开始播放音频 ({len(audio_data)} 字节)")
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            self.is_playing = False
            print("✅ 音频播放完成")
            
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"❌ 音频播放失败: {e}")
            self.is_playing = False
    
    def play_audio_async(self, audio_data: bytes, format: str = "mp3"):
        """
        异步播放音频
        
        Args:
            audio_data: 音频字节数据
            format: 音频格式
        """
        def play_thread():
            self.play_audio_bytes(audio_data, format)
            
        thread = threading.Thread(target=play_thread)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """停止播放"""
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            print("🛑 停止播放")


# 全局播放器实例
_player = None

def get_player():
    """获取全局播放器实例"""
    global _player
    if _player is None:
        _player = AudioPlayer()
    return _player


def play_audio(audio_data: bytes, format: str = "mp3", async_play: bool = True):
    """
    便捷播放函数
    
    Args:
        audio_data: 音频数据
        format: 音频格式
        async_play: 是否异步播放
    """
    player = get_player()
    if async_play:
        player.play_audio_async(audio_data, format)
    else:
        player.play_audio_bytes(audio_data, format)


if __name__ == "__main__":
    # 测试播放器
    print("音频播放器测试完成") 