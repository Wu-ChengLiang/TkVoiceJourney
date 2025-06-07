#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音直播弹幕语音客服系统 - 主应用
集成弹幕获取、AI判断、TTS语音合成功能
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "Fetcher"))

# 加载环境变量
load_dotenv(project_root / ".env")

# 导入项目模块
from barrage_fetcher import BarrageFetcher
from ai_judge import create_ai_judge
from tts_client import TTSClient
from data_analytics import analytics

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 设置为WARNING级别，过滤掉INFO消息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 设置特定模块的日志级别
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 主应用保持INFO级别

# 设置其他模块的日志级别
logging.getLogger("barrage_fetcher").setLevel(logging.WARNING)  # 弹幕获取器只显示警告和错误
logging.getLogger("ai_judge").setLevel(logging.INFO)  # AI判断保持INFO
logging.getLogger("tts_client").setLevel(logging.INFO)  # TTS客户端保持INFO
logging.getLogger("data_analytics").setLevel(logging.WARNING)  # 数据分析只显示警告和错误

# 过滤uvicorn和httpx的INFO日志
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# FastAPI应用
app = FastAPI(
    title="抖音直播弹幕语音客服",
    description="实时弹幕获取、AI智能回复、TTS语音合成",
    version="1.0.0"
)

# 静态文件服务
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.barrage_data: List[Dict] = []
        self.ai_responses: List[Dict] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
        
    async def broadcast(self, data: dict):
        """广播消息到所有连接的客户端"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# 数据模型
class LiveRoomRequest(BaseModel):
    live_id: str

class ManualReplyRequest(BaseModel):
    text: str

# 全局变量
barrage_fetcher: Optional[BarrageFetcher] = None
ai_judge = None
tts_client: Optional[TTSClient] = None
barrage_buffer: List[Dict] = []
last_ai_check_time = time.time()

# 弹幕数据缓冲区处理
async def process_barrage_buffer():
    """每8秒处理一次弹幕缓冲区"""
    global barrage_buffer, last_ai_check_time
    
    while True:
        await asyncio.sleep(8)  # 8秒间隔
        
        if not barrage_buffer:
            continue
            
        current_time = time.time()
        
        # 获取最近8秒的弹幕
        recent_barrages = [
            barrage for barrage in barrage_buffer 
            if current_time - barrage.get('timestamp', 0) <= 8
        ]
        
        if not recent_barrages:
            continue
            
        logger.info(f"处理 {len(recent_barrages)} 条弹幕")
        
        # AI判断弹幕价值
        if ai_judge:
            try:
                ai_result = await ai_judge.judge_barrages(recent_barrages)
                if ai_result and ai_result.get('has_value'):
                    # 生成商家回复
                    reply_text = await ai_judge.generate_reply(ai_result.get('content', ''))
                    if reply_text:
                        # TTS语音合成
                        if tts_client:
                            audio_path = await tts_client.text_to_speech(reply_text)
                            if audio_path:
                                # 广播AI回复和音频
                                await manager.broadcast({
                                    'type': 'ai_reply',
                                    'text': reply_text,
                                    'audio_path': audio_path,
                                    'timestamp': current_time
                                })
                                
                                # 保存AI回复记录
                                ai_response_data = {
                                    'text': reply_text,
                                    'audio_path': audio_path,
                                    'timestamp': current_time,
                                    'source_barrages': recent_barrages
                                }
                                manager.ai_responses.append(ai_response_data)
                                
                                # 添加到数据分析
                                analytics.add_ai_response(ai_response_data)
                        
            except Exception as e:
                logger.error(f"AI处理失败: {e}")
                
        # 清理过期的弹幕缓冲区
        barrage_buffer = [
            barrage for barrage in barrage_buffer 
            if current_time - barrage.get('timestamp', 0) <= 30  # 保留最近30秒
        ]

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页面"""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>抖音直播弹幕语音客服</title></head>
            <body>
                <h1>抖音直播弹幕语音客服系统</h1>
                <p>模板文件未找到，请检查 templates/index.html</p>
            </body>
        </html>
        """)

@app.post("/api/start_live")
async def start_live_monitoring(request: LiveRoomRequest):
    """开始监控直播间"""
    global barrage_fetcher
    
    try:
        if barrage_fetcher:
            await barrage_fetcher.stop()
            
        barrage_fetcher = BarrageFetcher(request.live_id)
        
        # 设置弹幕回调
        barrage_fetcher.set_callback(on_barrage_received)
        
        # 启动弹幕获取
        asyncio.create_task(barrage_fetcher.start())
        
        return {"status": "success", "message": f"开始监控直播间 {request.live_id}"}
        
    except Exception as e:
        logger.error(f"启动直播监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop_live")
async def stop_live_monitoring():
    """停止监控直播间"""
    global barrage_fetcher
    
    try:
        if barrage_fetcher:
            await barrage_fetcher.stop()
            barrage_fetcher = None
            
        return {"status": "success", "message": "已停止监控"}
        
    except Exception as e:
        logger.error(f"停止直播监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/manual_reply")
async def manual_reply(request: ManualReplyRequest):
    """手动回复"""
    try:
        if tts_client:
            audio_path = await tts_client.text_to_speech(request.text)
            if audio_path:
                await manager.broadcast({
                    'type': 'manual_reply',
                    'text': request.text,
                    'audio_path': audio_path,
                    'timestamp': time.time()
                })
                
        return {"status": "success", "message": "手动回复已发送"}
        
    except Exception as e:
        logger.error(f"手动回复失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test_mode")
async def start_test_mode():
    """启动测试模式"""
    try:
        # 导入测试弹幕生成器
        from test_barrage import generate_test_barrages
        
        # 启动测试弹幕生成
        asyncio.create_task(generate_test_barrages(on_barrage_received))
        
        return {"status": "success", "message": "测试模式已启动"}
        
    except Exception as e:
        logger.error(f"启动测试模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/barrage_data")
async def get_barrage_data():
    """获取弹幕数据"""
    return {
        "barrages": manager.barrage_data[-100:],  # 最近100条
        "ai_responses": manager.ai_responses[-50:],  # 最近50条AI回复
        "total_barrages": len(manager.barrage_data),
        "total_responses": len(manager.ai_responses)
    }

@app.get("/api/analytics")
async def get_analytics():
    """获取数据分析报告"""
    try:
        return analytics.get_comprehensive_report()
    except Exception as e:
        logger.error(f"获取分析数据失败: {e}")
        return {"error": str(e)}

@app.get("/api/analytics/realtime")
async def get_realtime_analytics():
    """获取实时分析数据"""
    try:
        return analytics.get_realtime_stats()
    except Exception as e:
        logger.error(f"获取实时分析数据失败: {e}")
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            logger.info(f"收到WebSocket消息: {data}")
            
            # 处理不同类型的消息
            if data.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)

# 弹幕回调函数
async def on_barrage_received(barrage_data: dict):
    """弹幕接收回调"""
    global barrage_buffer
    
    # 添加时间戳
    barrage_data['timestamp'] = time.time()
    
    # 保存到管理器
    manager.barrage_data.append(barrage_data)
    
    # 添加到数据分析
    analytics.add_barrage(barrage_data)
    
    # 添加到缓冲区
    barrage_buffer.append(barrage_data)
    
    # 广播弹幕数据
    await manager.broadcast({
        'type': 'barrage',
        'data': barrage_data
    })
    
    # 写入markdown文件
    await save_barrage_to_md(barrage_data)

async def save_barrage_to_md(barrage_data: dict):
    """保存弹幕到markdown文件"""
    try:
        md_file = Path(__file__).parent / "data" / f"barrage_{datetime.now().strftime('%Y%m%d')}.md"
        md_file.parent.mkdir(exist_ok=True)
        
        timestamp = datetime.fromtimestamp(barrage_data.get('timestamp', time.time()))
        content = f"\n## {timestamp.strftime('%H:%M:%S')}\n"
        content += f"**类型**: {barrage_data.get('type', 'unknown')}\n"
        content += f"**内容**: {barrage_data.get('content', '')}\n"
        content += f"**用户**: {barrage_data.get('user', '')}\n"
        content += f"**原始数据**: {json.dumps(barrage_data, ensure_ascii=False)}\n\n"
        
        with open(md_file, "a", encoding="utf-8") as f:
            f.write(content)
            
    except Exception as e:
        logger.error(f"保存弹幕到markdown失败: {e}")

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global ai_judge, tts_client
    
    # 加载环境变量
    load_dotenv()
    
    logger.info("🚀 启动抖音直播弹幕语音客服系统")
    
    # 创建必要目录
    (Path(__file__).parent / "data").mkdir(exist_ok=True)
    (Path(__file__).parent / "static" / "audio").mkdir(exist_ok=True, parents=True)
    
    # 初始化AI判断系统
    try:
        ai_judge = create_ai_judge()
        logger.info("✅ AI判断系统初始化成功")
    except Exception as e:
        logger.error(f"❌ AI判断系统初始化失败: {e}")
    
    # 初始化TTS客户端
    try:
        tts_client = TTSClient()
        logger.info("✅ TTS客户端初始化成功")
    except Exception as e:
        logger.error(f"❌ TTS客户端初始化失败: {e}")
    
    # 启动弹幕缓冲区处理
    asyncio.create_task(process_barrage_buffer())
    logger.info("✅ 弹幕处理任务已启动")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    global barrage_fetcher
    
    logger.info("🛑 关闭抖音直播弹幕语音客服系统")
    
    if barrage_fetcher:
        await barrage_fetcher.stop()

# 确保app变量在模块级别可用

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 