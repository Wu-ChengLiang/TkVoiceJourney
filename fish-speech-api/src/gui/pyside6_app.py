#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化的PySide6语音聊天界面
美观、优雅、简洁的设计
"""

import sys
import os
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QProgressBar, QSplitter, 
    QFrame, QScrollArea, QSizePolicy, QMessageBox, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QThread, QTimer, Signal, QPropertyAnimation, 
    QEasingCurve, QRect, QSize
)
from PySide6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QPainter, 
    QLinearGradient, QBrush
)

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stream_integration import StreamingVoiceChat
from core.audio_player import get_player


class ModernButton(QPushButton):
    """现代化按钮样式"""
    
    def __init__(self, text: str, primary: bool = False, icon_path: str = None):
        super().__init__(text)
        self.primary = primary
        self.setup_style()
        
    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #45a049);
                    border: none;
                    border-radius: 12px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 12px 24px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5CBF60, stop:1 #55b559);
                    transform: translateY(-2px);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3e8e41, stop:1 #357a38);
                }
                QPushButton:disabled {
                    background: #cccccc;
                    color: #666666;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    border: 2px solid #dee2e6;
                    border-radius: 12px;
                    color: #495057;
                    font-weight: 500;
                    font-size: 13px;
                    padding: 10px 20px;
                    min-height: 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    border-color: #adb5bd;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e9ecef, stop:1 #dee2e6);
                }
            """)


class StatusIndicator(QLabel):
    """状态指示器"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(12, 12)
        self.set_status("idle")
        
    def set_status(self, status: str):
        color_map = {
            "idle": "#6c757d",      # 灰色
            "connecting": "#ffc107", # 黄色
            "connected": "#28a745",  # 绿色
            "processing": "#007bff", # 蓝色
            "error": "#dc3545"       # 红色
        }
        
        color = color_map.get(status, "#6c757d")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)


class MessageBubble(QFrame):
    """消息气泡"""
    
    def __init__(self, message: str, is_user: bool = True, timestamp: str = None):
        super().__init__()
        self.setup_ui(message, is_user, timestamp)
        
    def setup_ui(self, message: str, is_user: bool, timestamp: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 消息内容
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # 时间戳
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        if is_user:
            # 用户消息 - 右对齐，蓝色背景
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #007bff, stop:1 #0056b3);
                    border-radius: 18px;
                    margin-left: 60px;
                    margin-right: 12px;
                    margin-bottom: 8px;
                }
            """)
            message_label.setStyleSheet("color: white; font-weight: 500;")
            time_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px;")
            time_label.setAlignment(Qt.AlignRight)
        else:
            # AI回复 - 左对齐，灰色背景
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    border-radius: 18px;
                    border: 1px solid #dee2e6;
                    margin-left: 12px;
                    margin-right: 60px;
                    margin-bottom: 8px;
                }
            """)
            message_label.setStyleSheet("color: #495057; font-weight: 400;")
            time_label.setAlignment(Qt.AlignLeft)
            
        layout.addWidget(message_label)
        layout.addWidget(time_label)


class ChatArea(QScrollArea):
    """聊天区域"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 聊天内容容器
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(4)
        
        self.setWidget(self.chat_widget)
        
        # 样式设置
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #dee2e6;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #adb5bd;
            }
        """)
        
    def add_message(self, message: str, is_user: bool = True):
        bubble = MessageBubble(message, is_user)
        self.chat_layout.addWidget(bubble)
        
        # 自动滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_messages(self):
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class ProcessingThread(QThread):
    """处理线程"""
    
    message_received = Signal(str)
    audio_generated = Signal(bytes)
    error_occurred = Signal(str)
    finished = Signal()
    
    def __init__(self, voice_chat: StreamingVoiceChat, user_input: str):
        super().__init__()
        self.voice_chat = voice_chat
        self.user_input = user_input
        
    def run(self):
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 音频回调
            def audio_callback(audio_data):
                self.audio_generated.emit(audio_data)
            
            # 处理语音聊天
            loop.run_until_complete(
                self.voice_chat.process_voice_chat(self.user_input, audio_callback)
            )
            
            self.message_received.emit("✅ 语音生成完成")
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


class VoiceChatMainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.voice_chat = StreamingVoiceChat()
        self.audio_player = get_player()
        self.processing_thread: Optional[ProcessingThread] = None
        
        self.setup_ui()
        self.setup_connections()
        self.test_connection()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("🎵 流式语音聊天系统 - Modern UI")
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置应用图标和样式
        self.setup_styles()
        
        # 中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部标题栏
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 聊天区域
        self.chat_area = ChatArea()
        main_layout.addWidget(self.chat_area, 1)
        
        # 底部输入区域
        input_area = self.create_input_area()
        main_layout.addWidget(input_area)
        
        # 添加欢迎消息
        self.chat_area.add_message("👋 欢迎使用流式语音聊天系统！\n请在下方输入您的问题，我会为您生成语音回答。", False)
        
    def setup_styles(self):
        """设置应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: "Segoe UI", "微软雅黑", Arial, sans-serif;
            }
        """)
        
    def create_header(self) -> QWidget:
        """创建顶部标题栏"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)
        
        # 标题
        title = QLabel("🎵 流式语音聊天系统")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        
        # 状态区域
        status_layout = QHBoxLayout()
        self.status_indicator = StatusIndicator()
        self.status_label = QLabel("正在初始化...")
        self.status_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            font-weight: 500;
        """)
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addLayout(status_layout)
        
        return header
        
    def create_input_area(self) -> QWidget:
        """创建输入区域"""
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout(input_frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在这里输入您的问题... (Ctrl+Enter 发送)")
        self.input_text.setMaximumHeight(120)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                line-height: 1.5;
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 发送按钮
        self.send_button = ModernButton("🎤 发送并生成语音", primary=True)
        self.send_button.setMinimumWidth(160)
        
        # 停止按钮
        self.stop_button = ModernButton("🛑 停止播放")
        
        # 清空按钮
        self.clear_button = ModernButton("🗑️ 清空对话")
        
        # 保存按钮
        self.save_button = ModernButton("💾 保存音频")
        
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #e9ecef;
                height: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007bff, stop:1 #0056b3);
                border-radius: 6px;
            }
        """)
        
        layout.addWidget(self.input_text)
        layout.addLayout(button_layout)
        layout.addWidget(self.progress_bar)
        
        return input_frame
        
    def setup_connections(self):
        """设置信号连接"""
        self.send_button.clicked.connect(self.send_message)
        self.stop_button.clicked.connect(self.stop_audio)
        self.clear_button.clicked.connect(self.clear_chat)
        self.save_button.clicked.connect(self.save_audio)
        
        # 快捷键
        self.input_text.keyPressEvent = self.input_key_press_event
        
    def input_key_press_event(self, event):
        """处理输入框按键事件"""
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.send_message()
        else:
            QTextEdit.keyPressEvent(self.input_text, event)
            
    def test_connection(self):
        """测试连接"""
        self.update_status("connecting", "正在测试连接...")
        
        def test_thread():
            try:
                if self.voice_chat.test_connection():
                    self.update_status("connected", "连接正常，可以开始对话")
                else:
                    self.update_status("error", "连接失败，请检查服务")
            except Exception as e:
                self.update_status("error", f"连接测试错误: {e}")
        
        threading.Thread(target=test_thread, daemon=True).start()
        
    def update_status(self, status: str, message: str):
        """更新状态"""
        def update():
            self.status_indicator.set_status(status)
            self.status_label.setText(message)
        
        if threading.current_thread() != threading.main_thread():
            QTimer.singleShot(0, update)
        else:
            update()
            
    def send_message(self):
        """发送消息"""
        user_input = self.input_text.toPlainText().strip()
        
        if not user_input:
            QMessageBox.warning(self, "警告", "请输入内容!")
            return
            
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.information(self, "提示", "正在处理中，请等待...")
            return
            
        # 添加用户消息到聊天区域
        self.chat_area.add_message(user_input, True)
        
        # 清空输入框
        self.input_text.clear()
        
        # 更新UI状态
        self.send_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.update_status("processing", "正在生成回答...")
        
        # 启动处理线程
        self.processing_thread = ProcessingThread(self.voice_chat, user_input)
        self.processing_thread.message_received.connect(self.on_message_received)
        self.processing_thread.audio_generated.connect(self.on_audio_generated)
        self.processing_thread.error_occurred.connect(self.on_error_occurred)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()
        
    def on_message_received(self, message: str):
        """处理接收到的消息"""
        self.chat_area.add_message(message, False)
        
    def on_audio_generated(self, audio_data: bytes):
        """处理生成的音频"""
        try:
            # 获取项目根目录的output路径
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = output_dir / f"voice_chat_{timestamp}.mp3"
            
            with open(audio_file, "wb") as f:
                f.write(audio_data)
                
            # 播放音频
            self.audio_player.play_audio_async(audio_data)
            
            # 添加消息
            message = f"🎵 音频已生成并开始播放 ({len(audio_data)} 字节)\n💾 已保存到: {audio_file.relative_to(project_root)}"
            self.chat_area.add_message(message, False)
            
        except Exception as e:
            self.on_error_occurred(f"音频处理失败: {e}")
            
    def on_error_occurred(self, error: str):
        """处理错误"""
        self.chat_area.add_message(f"❌ 错误: {error}", False)
        self.update_status("error", f"处理失败: {error}")
        
    def on_processing_finished(self):
        """处理完成"""
        self.send_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.update_status("connected", "就绪")
        
    def stop_audio(self):
        """停止音频播放"""
        try:
            self.audio_player.stop()
            self.chat_area.add_message("🛑 音频播放已停止", False)
        except Exception as e:
            self.chat_area.add_message(f"停止播放失败: {e}", False)
            
    def clear_chat(self):
        """清空对话"""
        self.chat_area.clear_messages()
        self.chat_area.add_message("👋 对话已清空，可以开始新的对话！", False)
        
    def save_audio(self):
        """保存音频提示"""
        QMessageBox.information(
            self, 
            "保存音频", 
            "生成的音频会自动保存到 output/ 目录中\n\n文件命名格式：voice_chat_YYYYMMDD_HHMMSS.mp3"
        )
        
    def closeEvent(self, event):
        """关闭事件"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "正在处理中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.processing_thread.terminate()
                self.processing_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("TkVoiceJourney")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("TkVoiceJourney")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = VoiceChatMainWindow()
    window.show()
    
    # 运行应用
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("用户中断")
    except Exception as e:
        print(f"应用错误: {e}")


if __name__ == "__main__":
    main() 