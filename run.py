#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音直播弹幕语音客服系统 - 启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """启动服务器"""
    # 获取项目根目录
    project_root = Path(__file__).parent
    app_dir = project_root / "app"
    
    # 检查app目录是否存在
    if not app_dir.exists():
        print("❌ 错误: app 目录不存在")
        sys.exit(1)
    
    # 检查main.py是否存在
    main_file = app_dir / "main.py"
    if not main_file.exists():
        print("❌ 错误: app/main.py 文件不存在")
        sys.exit(1)
    
    print("🚀 启动抖音直播弹幕语音客服系统...")
    print(f"📁 项目目录: {project_root}")
    print(f"🌐 服务器地址: http://localhost:8000")
    print("=" * 50)
    
    # 切换到app目录并启动uvicorn
    try:
        os.chdir(app_dir)
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 