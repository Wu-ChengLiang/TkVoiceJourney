#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的TK语音聊天界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import asyncio
import sys
import os

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stream_integration import StreamingVoiceChat
from core.audio_player import get_player


class VoiceChatApp:
    def __init__(self, root):
        """初始化TK应用"""
        self.root = root
        self.root.title("流式语音聊天 - VLLM + Fish Audio")
        self.root.geometry("800x600")
        
        # 初始化后端
        self.voice_chat = StreamingVoiceChat()
        self.audio_player = get_player()
        
        # 创建UI
        self.create_widgets()
        
        # 测试连接
        self.test_connection()
        
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎵 流式语音聊天系统", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="🔄 正在初始化...", foreground="orange")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # 输入框标签
        input_label = ttk.Label(main_frame, text="输入您的问题:")
        input_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        # 输入框
        self.input_text = tk.Text(main_frame, height=3, width=60, wrap=tk.WORD)
        self.input_text.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        # 发送按钮
        self.send_button = ttk.Button(button_frame, text="🎤 发送并生成语音", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止按钮
        self.stop_button = ttk.Button(button_frame, text="🛑 停止播放", command=self.stop_audio)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空按钮
        clear_button = ttk.Button(button_frame, text="🗑️ 清空", command=self.clear_input)
        clear_button.pack(side=tk.LEFT)
        
        # 对话历史标签
        history_label = ttk.Label(main_frame, text="对话历史:")
        history_label.grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        # 对话历史文本框
        self.history_text = scrolledtext.ScrolledText(main_frame, height=15, width=80, wrap=tk.WORD, state=tk.DISABLED)
        self.history_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # 绑定回车键
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
        
    def test_connection(self):
        """测试连接"""
        def test_thread():
            try:
                if self.voice_chat.test_connection():
                    self.update_status("✅ 连接正常，可以开始对话", "green")
                else:
                    self.update_status("❌ 连接失败，请检查服务", "red")
            except Exception as e:
                self.update_status(f"❌ 连接测试错误: {e}", "red")
        
        threading.Thread(target=test_thread, daemon=True).start()
        
    def update_status(self, message, color="black"):
        """更新状态"""
        self.root.after(0, lambda: self.status_label.config(text=message, foreground=color))
        
    def add_to_history(self, message):
        """添加到对话历史"""
        def update():
            self.history_text.config(state=tk.NORMAL)
            self.history_text.insert(tk.END, message + "\n\n")
            self.history_text.see(tk.END)
            self.history_text.config(state=tk.DISABLED)
        
        self.root.after(0, update)
        
    def send_message(self):
        """发送消息"""
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("警告", "请输入内容!")
            return
            
        # 禁用发送按钮
        self.send_button.config(state=tk.DISABLED)
        self.update_status("🔄 正在处理中...", "orange")
        
        # 添加到历史
        self.add_to_history(f"👤 用户: {user_input}")
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 异步处理
        def process_thread():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 定义音频播放回调
                def play_audio_callback(audio_data):
                    self.add_to_history(f"🎵 开始播放语音回答 ({len(audio_data)} 字节)")
                    self.audio_player.play_audio_async(audio_data)
                
                # 处理语音聊天
                loop.run_until_complete(
                    self.voice_chat.process_voice_chat(user_input, play_audio_callback)
                )
                
                self.add_to_history("✅ 语音生成完成")
                self.update_status("✅ 处理完成", "green")
                
            except Exception as e:
                error_msg = f"❌ 处理失败: {e}"
                self.add_to_history(error_msg)
                self.update_status(error_msg, "red")
            finally:
                # 重新启用发送按钮
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
        
        threading.Thread(target=process_thread, daemon=True).start()
        
    def stop_audio(self):
        """停止音频播放"""
        try:
            self.audio_player.stop()
            self.add_to_history("🛑 音频播放已停止")
        except Exception as e:
            self.add_to_history(f"停止播放失败: {e}")
            
    def clear_input(self):
        """清空输入框"""
        self.input_text.delete("1.0", tk.END)


def main():
    """主函数"""
    root = tk.Tk()
    app = VoiceChatApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("用户中断")
    except Exception as e:
        print(f"应用错误: {e}")


if __name__ == "__main__":
    main() 