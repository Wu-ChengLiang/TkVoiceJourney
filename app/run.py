#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音直播弹幕语音客服系统 - 启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)
    
    try:
        import uvicorn
        
        print("🚀 启动抖音直播弹幕语音客服系统")
        print("📱 访问地址: http://localhost:8000")
        print("🛑 按 Ctrl+C 停止服务")
        print("=" * 50)
        
        # 不使用reload模式，避免模块导入问题
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1) 