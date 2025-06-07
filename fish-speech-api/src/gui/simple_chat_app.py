#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简洁的语音聊天界面 - 使用OpenAI兼容API
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import asyncio
import sys
import os
import base64

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.openai_compatible import OpenAI, OpenAICompatibleClient
from core.audio_player import get_player


class SimpleChatApp:
    def __init__(self, root):
        """初始化简洁聊天应用"""
        self.root = root
        self.root.title("🎵 TkVoiceJourney - 语音聊天")
        self.root.geometry("900x700")
        
        # 初始化客户端
        try:
            self.openai_client = OpenAI()
            self.compatible_client = OpenAICompatibleClient()
            self.audio_player = get_player()
            self.is_processing = False
        except Exception as e:
            messagebox.showerror("初始化错误", f"客户端初始化失败: {e}")
            self.root.destroy()
            return
        
        # 创建UI
        self.create_widgets()
        
        # 启动时健康检查
        self.check_health()
        
    def create_widgets(self):
        """创建UI组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🎵 TkVoiceJourney", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # 状态指示器
        self.status_label = ttk.Label(title_frame, text="🔄 检查中...", font=("Arial", 10))
        self.status_label.pack(side=tk.RIGHT)
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="💬 输入消息", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 输入文本框
        self.input_text = tk.Text(input_frame, height=4, wrap=tk.WORD, font=("Arial", 11))
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 输入滚动条
        input_scroll = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        input_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.input_text.config(yscrollcommand=input_scroll.set)
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        self.send_button = ttk.Button(button_frame, text="🚀 发送并生成语音", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_button = ttk.Button(button_frame, text="🗑️ 清空", command=self.clear_input)
        clear_button.pack(side=tk.LEFT)
        
        # 对话历史区域
        history_frame = ttk.LabelFrame(main_frame, text="📝 对话历史", padding="10")
        history_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # 历史文本框
        self.history_text = scrolledtext.ScrolledText(
            history_frame, 
            wrap=tk.WORD, 
            font=("Arial", 10),
            state=tk.DISABLED,
            height=20
        )
        self.history_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        input_frame.columnconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # 快捷键绑定
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
        self.input_text.bind('<Shift-Return>', lambda e: None)  # 允许Shift+Enter换行
        
        # 插入欢迎信息
        self.add_system_message("欢迎使用TkVoiceJourney！输入文本后点击发送，系统将生成语音回答。")
        self.add_system_message("快捷键：Ctrl+Enter 发送消息")
        
    def check_health(self):
        """检查系统健康状态"""
        def health_check():
            try:
                # 异步健康检查
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                health = loop.run_until_complete(self.compatible_client.health_check())
                
                if health['status'] == 'healthy':
                    self.update_status("✅ 系统正常", "green")
                    self.add_system_message("✅ 系统健康检查通过，所有组件运行正常")
                else:
                    self.update_status("❌ 系统异常", "red")
                    self.add_system_message("❌ 系统健康检查失败，请检查配置")
                    for component, status in health['components'].items():
                        if status != 'ok':
                            self.add_system_message(f"  - {component.upper()}: {status}")
                
                loop.close()
                
            except Exception as e:
                self.update_status("❌ 检查失败", "red")
                self.add_system_message(f"❌ 健康检查失败: {e}")
        
        threading.Thread(target=health_check, daemon=True).start()
        
    def update_status(self, message, color="black"):
        """更新状态标签"""
        self.root.after(0, lambda: self.status_label.config(text=message, foreground=color))
        
    def add_system_message(self, message):
        """添加系统消息"""
        self.add_to_history(f"🤖 系统: {message}", "blue")
        
    def add_to_history(self, message, color="black"):
        """添加消息到历史记录"""
        def update():
            self.history_text.config(state=tk.NORMAL)
            
            # 插入时间戳
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 插入消息
            start_pos = self.history_text.index(tk.END + "-1c")
            self.history_text.insert(tk.END, f"[{timestamp}] {message}\n\n")
            end_pos = self.history_text.index(tk.END + "-1c")
            
            # 设置颜色
            if color != "black":
                tag_name = f"color_{color}"
                self.history_text.tag_config(tag_name, foreground=color)
                self.history_text.tag_add(tag_name, start_pos, end_pos)
            
            # 滚动到底部
            self.history_text.see(tk.END)
            self.history_text.config(state=tk.DISABLED)
        
        self.root.after(0, update)
        
    def send_message(self):
        """发送消息并处理回复"""
        if self.is_processing:
            return
            
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("提示", "请输入消息内容！")
            return
        
        # 开始处理
        self.is_processing = True
        self.send_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start(10)
        self.update_status("🔄 处理中...", "orange")
        
        # 添加用户消息到历史
        self.add_to_history(f"👤 用户: {user_input}", "darkgreen")
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 异步处理
        def process_message():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 使用集成的流式对话+TTS功能
                loop.run_until_complete(self._process_with_tts(user_input))
                
                loop.close()
                
            except Exception as e:
                self.add_to_history(f"❌ 处理失败: {e}", "red")
            finally:
                # 恢复UI状态
                self._finish_processing()
        
        threading.Thread(target=process_message, daemon=True).start()
        
    async def _process_with_tts(self, user_input):
        """处理消息并生成TTS"""
        try:
            assistant_response = ""
            received_audio = False
            
            # 显示助手开始回复
            self.add_to_history("🤖 助手: ", "blue")
            
            # 使用流式对话+TTS集成
            stream = self.compatible_client.stream_chat_with_tts(
                user_input=user_input,
                system_prompt="你是一个友好的助手，用简洁明了的语言回答问题。",
                enable_tts=True
            )
            
            async for chunk in stream:
                if not self.is_processing:  # 检查是否被停止
                    break
                    
                if chunk['type'] == 'text':
                    content = chunk['content']
                    assistant_response += content
                    
                    # 实时更新显示
                    self.root.after(0, lambda c=content: self._append_assistant_text(c))
                    
                elif chunk['type'] == 'audio':
                    # 处理音频数据
                    audio_data = base64.b64decode(chunk['content'])
                    self.add_to_history(f"🎵 生成语音 ({len(audio_data)} 字节)", "purple")
                    received_audio = True
                    
                    # 播放音频 - 增强错误处理
                    try:
                        # 保存音频文件以便调试
                        import time
                        audio_filename = f"debug_audio_{int(time.time())}.mp3"
                        with open(audio_filename, "wb") as f:
                            f.write(audio_data)
                        self.add_to_history(f"💾 音频已保存: {audio_filename}", "gray")
                        
                        # 播放音频
                        self.audio_player.play_audio_async(audio_data, "mp3")
                        self.add_to_history("🔊 音频开始播放", "green")
                        
                    except Exception as audio_error:
                        self.add_to_history(f"❌ 音频播放失败: {audio_error}", "red")
                        # 尝试系统默认播放器
                        try:
                            import subprocess
                            subprocess.Popen(['start', audio_filename], shell=True)
                            self.add_to_history("🎵 尝试用系统播放器播放", "orange")
                        except:
                            pass
                    
                elif chunk['type'] == 'error':
                    self.add_to_history(f"❌ TTS错误: {chunk['content']}", "red")
            
            if assistant_response:
                self.add_to_history("✅ 回复完成", "green")
                
                # 如果没有收到音频，尝试手动生成
                if not received_audio:
                    self.add_to_history("⚠️ 未收到音频数据，尝试手动生成TTS...", "orange")
                    try:
                        manual_audio = await self.compatible_client.tts_client.simple_tts(assistant_response)
                        if manual_audio:
                            # 保存并播放手动生成的音频
                            import time
                            manual_filename = f"manual_audio_{int(time.time())}.mp3"
                            with open(manual_filename, "wb") as f:
                                f.write(manual_audio)
                            
                            self.add_to_history(f"🎵 手动生成音频成功 ({len(manual_audio)} 字节)", "blue")
                            self.audio_player.play_audio_async(manual_audio, "mp3")
                            
                    except Exception as manual_error:
                        self.add_to_history(f"❌ 手动TTS失败: {manual_error}", "red")
            else:
                self.add_to_history("⚠️ 未收到回复内容", "orange")
                
        except Exception as e:
            self.add_to_history(f"❌ 处理异常: {e}", "red")
            import traceback
            error_details = traceback.format_exc()
            self.add_to_history(f"🔍 错误详情: {error_details}", "gray")
            
    def _append_assistant_text(self, text):
        """实时追加助手文本"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert(tk.END, text)
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
        
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
        self.audio_player.stop()
        self.add_to_history("🛑 处理已停止", "orange")
        self._finish_processing()
        
    def _finish_processing(self):
        """完成处理，恢复UI状态"""
        self.root.after(0, lambda: [
            setattr(self, 'is_processing', False),
            self.send_button.config(state=tk.NORMAL),
            self.stop_button.config(state=tk.DISABLED),
            self.progress.stop(),
            self.update_status("✅ 就绪", "green")
        ])
        
    def clear_input(self):
        """清空输入框"""
        self.input_text.delete("1.0", tk.END)
        
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.is_processing:
            if messagebox.askokcancel("确认", "正在处理中，确定要退出吗？"):
                self.stop_processing()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    # 设置高DPI支持
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = SimpleChatApp(root)
    
    # 绑定窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n用户中断退出")
    except Exception as e:
        print(f"应用程序错误: {e}")


if __name__ == "__main__":
    main() 