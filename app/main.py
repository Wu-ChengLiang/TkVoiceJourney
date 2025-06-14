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
from ai_judge_simple import create_ai_judge
from tts_client import create_tts_client
from data_analytics import analytics

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 设置为WARNING级别，过滤掉INFO消息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 设置特定模块的日志级别
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 主应用启用DEBUG级别调试

# 设置其他模块的日志级别
logging.getLogger("barrage_fetcher").setLevel(logging.WARNING)  # 弹幕获取器只显示警告和错误
logging.getLogger("ai_judge").setLevel(logging.DEBUG)  # AI判断启用DEBUG级别调试
logging.getLogger("ai_judge_simple").setLevel(logging.DEBUG)  # AI判断简化版也启用DEBUG
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
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
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
tts_client = None
barrage_buffer: List[Dict] = []
last_ai_check_time = time.time()

# 智能弹幕处理系统 - 使用OpenAI+Fish Audio流式语音回复
async def process_barrage_intelligently():
    """智能弹幕处理 - 每次筛选后都调用OpenAI+Fish Audio生成语音回复"""
    global barrage_buffer
    
    while True:
        await asyncio.sleep(2)  # 1秒检查一次
        
        if not barrage_buffer:
            continue
            
        current_time = time.time()
        
        # 处理新弹幕
        new_barrages = []
        for barrage in barrage_buffer:
            if not barrage.get('processed', False):
                new_barrages.append(barrage)
                barrage['processed'] = True
        
        if not new_barrages:
            continue
            
        # 使用优化版AI判断器筛选有价值的弹幕并生成OpenAI回复
        if ai_judge and hasattr(ai_judge, 'process_barrage_stream'):
            for barrage in new_barrages:
                try:
                    # 调试：打印弹幕数据结构
                    # logger.debug(f"🔍 处理弹幕数据: {barrage}")
                    
                    # 直接使用process_barrage_stream处理弹幕（已包含筛选+回复生成）
                    reply_text = await ai_judge.process_barrage_stream(barrage)
                    
                    if reply_text:
                        # logger.info(f"🎯 筛选出有价值弹幕，生成回复: {reply_text}")
                        # 调用Fish Audio生成语音
                        await _handle_openai_fish_reply(reply_text, [barrage], current_time)
                        # 限制频率，避免过于频繁回复
                        await asyncio.sleep(5)
                        break  # 一次只处理一条，避免同时回复多条
                    else:
                        logger.debug(f"❌ 弹幕未通过筛选: {barrage.get('content', '')[:30]}...")
                        
                except Exception as e:
                    logger.error(f"智能处理弹幕失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        # 兼容旧版AI判断器
        elif ai_judge:
            try:
                ai_result = await ai_judge.judge_barrages(new_barrages)
                if ai_result and ai_result.get('has_value'):
                    # 调用OpenAI生成回复
                    reply_text = await ai_judge.generate_reply(ai_result.get('content', ''))
                    if reply_text:
                        await _handle_openai_fish_reply(reply_text, new_barrages, current_time)
                        await asyncio.sleep(5)  # 限制频率
                        
            except Exception as e:
                logger.error(f"AI处理失败: {e}")
                
        # 清理过期的弹幕缓冲区
        barrage_buffer = [
            barrage for barrage in barrage_buffer 
            if current_time - barrage.get('timestamp', 0) <= 60  # 保留最近60秒
        ]

async def _handle_openai_fish_reply(reply_text: str, source_barrages: List[Dict], timestamp: float):
    """处理OpenAI+Fish Audio流式语音回复"""
    try:
        # logger.info(f"🤖 OpenAI生成回复: {reply_text}")
        
        # 使用Fish Audio WebSocket TTS生成语音（流式）
        audio_path = None
        if tts_client:
            audio_path = await tts_client.text_to_speech(reply_text)
            # if audio_path:
                # logger.info(f"🎵 Fish Audio语音已生成: {audio_path}")
        
        # 广播AI回复
        await manager.broadcast({
            'type': 'ai_reply',
            'text': reply_text,
            'audio_path': audio_path,
            'timestamp': timestamp,
            'source_content': source_barrages[0].get('content', '') if source_barrages else '',
            'generation_method': 'OpenAI+FishAudio'
        })
        
        # 保存AI回复记录
        ai_response_data = {
            'text': reply_text,
            'audio_path': audio_path,
            'timestamp': timestamp,
            'source_barrages': source_barrages,
            'generation_method': 'OpenAI+FishAudio'
        }
        manager.ai_responses.append(ai_response_data)
        
        # 添加到数据分析
        analytics.add_ai_response(ai_response_data)
        
        # logger.info(f"✅ OpenAI+Fish Audio流式回复完成: {reply_text}")
        
    except Exception as e:
        logger.error(f"处理OpenAI+Fish Audio回复失败: {e}")

async def _handle_ai_reply(reply_text: str, source_barrages: List[Dict], timestamp: float):
    """处理AI回复（兼容旧版本）"""
    await _handle_openai_fish_reply(reply_text, source_barrages, timestamp)

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
    """手动回复（支持OpenAI语音流式回复）"""
    try:
        reply_text = request.text
        
        # 如果需要使用OpenAI生成回复（当输入为空或特殊指令时）
        if not reply_text.strip() or reply_text.strip().startswith("@ai"):
            # 获取最近的弹幕作为上下文
            recent_barrages = barrage_buffer[-5:] if barrage_buffer else []
            if recent_barrages and ai_judge:
                context = recent_barrages[-1].get('content', '客户咨询')
                reply_text = await ai_judge.generate_reply(context)
                if not reply_text:
                    reply_text = "您好，感谢您的咨询，具体信息请联系我们的客服"
        
        # 使用Fish Audio TTS生成语音（流式）
        if tts_client and reply_text:
            audio_path = await tts_client.text_to_speech(reply_text)
            if audio_path:
                await manager.broadcast({
                    'type': 'manual_reply',
                    'text': reply_text,
                    'audio_path': audio_path,
                    'timestamp': time.time(),
                    'is_ai_generated': request.text.strip().startswith("@ai") or not request.text.strip()
                })
                
                # logger.info(f"✅ 手动回复已发送: {reply_text}")
                return {"status": "success", "message": "手动回复已发送", "reply_text": reply_text}
        
        return {"status": "error", "message": "语音生成失败"}
        
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

@app.get("/api/ai_stats")
async def get_ai_stats():
    """获取AI判断器统计信息"""
    try:
        if ai_judge and hasattr(ai_judge, 'get_stats'):
            return ai_judge.get_stats()
        else:
            return {
                "total_processed": 0,
                "ignored_count": 0,
                "ai_calls": 0,
                "cache_hits": 0,
                "batch_processed": 0,
                "message": "使用简化版AI判断器"
            }
    except Exception as e:
        logger.error(f"获取AI统计信息失败: {e}")
        return {"error": str(e)}

@app.get("/api/tts_status")
async def get_tts_status():
    """获取TTS服务状态"""
    try:
        if not tts_client:
            return {
                "status": "disconnected",
                "message": "TTS客户端未初始化",
                "type": "none"
            }
        
        # 检查TTS客户端类型
        tts_type = type(tts_client).__name__
        
        if tts_type == "SimpleTTSClient":
            return {
                "status": "disconnected", 
                "message": "使用简化版TTS客户端（无语音输出）",
                "type": "simple"
            }
        
        # 尝试简单的TTS测试
        try:
            # 检查Fish Audio配置
            from config import FISH_AUDIO_CONFIG
            if not FISH_AUDIO_CONFIG.get("api_key") or not FISH_AUDIO_CONFIG.get("voice_id"):
                return {
                    "status": "disconnected",
                    "message": "Fish Audio API配置不完整",
                    "type": "config_error"
                }
            
            # 如果有WebSocket TTS客户端，检查其连接状态
            if hasattr(tts_client, 'fish_tts'):
                return {
                    "status": "connected",
                    "message": "Fish Audio TTS服务可用",
                    "type": "fish_audio"
                }
            else:
                return {
                    "status": "connected",
                    "message": "TTS客户端已就绪",
                    "type": "streaming"
                }
                
        except Exception as test_error:
            logger.error(f"TTS测试失败: {test_error}")
            return {
                "status": "error",
                "message": f"TTS测试失败: {str(test_error)}",
                "type": "error"
            }
            
    except Exception as e:
        logger.error(f"获取TTS状态失败: {e}")
        return {
            "status": "error", 
            "message": f"状态检查失败: {str(e)}",
            "type": "error"
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            # logger.info(f"收到WebSocket消息: {data}")
            
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
    
    # logger.info("🚀 启动抖音直播弹幕语音客服系统")
    
    # 创建必要目录
    (Path(__file__).parent / "data").mkdir(exist_ok=True)
    (Path(__file__).parent / "static" / "audio").mkdir(exist_ok=True, parents=True)
    
    # 初始化AI判断系统
    try:
        ai_judge = create_ai_judge()
        # logger.info("✅ AI判断系统初始化成功")
    except Exception as e:
        logger.error(f"❌ AI判断系统初始化失败: {e}")
    
    # 初始化TTS客户端
    try:
        tts_client = create_tts_client()
        # logger.info("✅ TTS客户端初始化成功")
    except Exception as e:
        logger.error(f"❌ TTS客户端初始化失败: {e}")
    
    # 启动智能弹幕处理（OpenAI+Fish Audio流式语音回复）
    asyncio.create_task(process_barrage_intelligently())
    # logger.info("✅ 智能弹幕处理任务已启动（OpenAI+Fish Audio流式语音回复）")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    global barrage_fetcher
    
    # logger.info("🛑 关闭抖音直播弹幕语音客服系统")
    
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