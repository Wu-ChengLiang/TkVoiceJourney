#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单启动脚本
"""

import sys
import os
from pathlib import Path

# 确保当前目录在sys.path中
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent / "Fetcher"))

if __name__ == "__main__":
    try:
        # 直接导入并运行
        from main import app
        import uvicorn
        
        print("🚀 启动抖音直播弹幕语音客服系统")
        print("📱 访问地址: http://localhost:8000")
        print("🛑 按 Ctrl+C 停止服务")
        print("=" * 50)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 