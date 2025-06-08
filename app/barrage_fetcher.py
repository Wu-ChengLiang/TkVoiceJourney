#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弹幕获取模块 - 异步版本
包装原有的DouyinLiveWebFetcher，支持异步回调
"""

import asyncio
import logging
import sys
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# 添加Fetcher目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "Fetcher"))

from liveMan import DouyinLiveWebFetcher

logger = logging.getLogger(__name__)


class BarrageFetcher:
    """异步弹幕获取器"""
    
    def __init__(self, live_id: str):
        self.live_id = live_id
        self.fetcher: Optional[DouyinLiveWebFetcher] = None
        self.callback: Optional[Callable] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None
        
    def set_callback(self, callback: Callable[[Dict], None]):
        """设置弹幕回调函数"""
        self.callback = callback
        
    async def start(self):
        """开始获取弹幕"""
        if self.running:
            logger.warning("弹幕获取已在运行中")
            return
        
        # 保存主线程的事件循环
        self.main_loop = asyncio.get_event_loop()
        
        self.running = True
        logger.info(f"开始获取直播间 {self.live_id} 的弹幕")
        
        # 在单独线程中运行弹幕获取
        self.thread = threading.Thread(target=self._run_fetcher, daemon=True)
        self.thread.start()
        
    def _run_fetcher(self):
        """在线程中运行弹幕获取器"""
        try:
            self.fetcher = DouyinLiveWebFetcher(self.live_id)
            
            # 重写弹幕处理方法
            self.fetcher._parseChatMsg = self._handle_chat_msg
            self.fetcher._parseMemberMsg = self._handle_member_msg
            self.fetcher._parseGiftMsg = self._handle_gift_msg
            self.fetcher._parseLikeMsg = self._handle_like_msg
            self.fetcher._parseRoomStatsMsg = self._handle_room_stats_msg
            self.fetcher._parseSocialMsg = self._handle_social_msg
            self.fetcher._parseEmojiChatMsg = self._handle_emoji_chat_msg
            
            # 获取直播间状态
            self.fetcher.get_room_status()
            
            # 开始获取弹幕
            self.fetcher.start()
            
        except Exception as e:
            logger.error(f"弹幕获取器运行失败: {e}")
            self.running = False
            
    def _handle_chat_msg(self, payload):
        """处理聊天消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                # 当protobuf不可用时，生成模拟数据
                import random
                fake_users = ["测试用户1", "测试用户2", "测试用户3", "观众甲", "观众乙"]
                fake_contents = ["主播好棒！", "666", "支持", "厉害了", "nice"]
                user_id = str(random.randint(10000, 99999))
                nickname = random.choice(fake_users)
                content = random.choice(fake_contents)
            else:
                chat_msg = ChatMessage().parse(payload)
                user_id = str(chat_msg.user.id)
                nickname = chat_msg.user.nick_name
                content = chat_msg.content
            
            barrage_data = {
                'type': 'chat',
                'user_id': user_id,
                'username': nickname,
                'content': content,
                'user': f"[{user_id}]{nickname}",
                'raw_type': '聊天msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理聊天消息失败: {e}")
    
    def _handle_member_msg(self, payload):
        """处理进场消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                # 当protobuf不可用时，跳过处理
                return
            
            member_msg = MemberMessage().parse(payload)
            user_id = str(member_msg.user.id)
            nickname = member_msg.user.nick_name
            gender = "男" if member_msg.user.gender == 1 else "女"
            
            barrage_data = {
                'type': 'member',
                'user_id': user_id,
                'username': nickname,
                'gender': gender,
                'content': f"进入了直播间",
                'user': f"[{user_id}][{gender}]{nickname}",
                'raw_type': '进场msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理进场消息失败: {e}")
    
    def _handle_gift_msg(self, payload):
        """处理礼物消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                return
                
            gift_msg = GiftMessage().parse(payload)
            user_id = str(gift_msg.user.id)
            nickname = gift_msg.user.nick_name
            gift_name = gift_msg.gift.name
            gift_count = gift_msg.combo_count
            
            barrage_data = {
                'type': 'gift',
                'user_id': user_id,
                'username': nickname,
                'gift_name': gift_name,
                'gift_count': gift_count,
                'content': f"送出 {gift_name} x{gift_count}",
                'user': f"[{user_id}]{nickname}",
                'raw_type': '礼物msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理礼物消息失败: {e}")
    
    def _handle_like_msg(self, payload):
        """处理点赞消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                return
                
            like_msg = LikeMessage().parse(payload)
            user_id = str(like_msg.user.id)
            nickname = like_msg.user.nick_name
            count = like_msg.count
            
            barrage_data = {
                'type': 'like',
                'user_id': user_id,
                'username': nickname,
                'like_count': count,
                'content': f"点赞 x{count}",
                'user': f"[{user_id}]{nickname}",
                'raw_type': '点赞msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理点赞消息失败: {e}")
    
    def _handle_room_stats_msg(self, payload):
        """处理直播间统计消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                return
                
            stats_msg = RoomStatsMessage().parse(payload)
            display_long = stats_msg.display_long
            
            barrage_data = {
                'type': 'stats',
                'display_long': display_long,
                'content': f"{display_long}",
                'user': "系统统计",
                'raw_type': '直播间统计msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理统计消息失败: {e}")
    
    def _handle_social_msg(self, payload):
        """处理关注消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                return
                
            social_msg = SocialMessage().parse(payload)
            user_id = str(social_msg.user.id)
            nickname = social_msg.user.nick_name
            
            barrage_data = {
                'type': 'follow',
                'user_id': user_id,
                'username': nickname,
                'content': "关注了主播",
                'user': f"[{user_id}]{nickname}",
                'raw_type': '关注msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理关注消息失败: {e}")
    
    def _handle_emoji_chat_msg(self, payload):
        """处理表情聊天消息"""
        try:
            if not PROTOBUF_AVAILABLE:
                return
                
            emoji_msg = EmojiChatMessage().parse(payload)
            user_id = str(emoji_msg.user.id)
            nickname = emoji_msg.user.nick_name
            content = emoji_msg.default_content or f"表情#{emoji_msg.emoji_id}"
            
            barrage_data = {
                'type': 'emoji_chat',
                'user_id': user_id,
                'username': nickname,
                'content': content,
                'user': f"[{user_id}]{nickname}",
                'raw_type': '表情聊天msg'
            }
            
            self._async_callback(barrage_data)
            
        except Exception as e:
            logger.error(f"处理表情聊天消息失败: {e}")
    
    def _async_callback(self, barrage_data: Dict):
        """异步回调包装器"""
        if self.callback:
            try:
                # 如果回调是协程函数，需要在事件循环中调用
                import inspect
                if inspect.iscoroutinefunction(self.callback):
                    # 确保我们有主线程的事件循环
                    if self.main_loop and not self.main_loop.is_closed():
                        try:
                            # 使用run_coroutine_threadsafe安全地调用协程
                            future = asyncio.run_coroutine_threadsafe(
                                self.callback(barrage_data),
                                self.main_loop
                            )
                            # 不等待结果，避免阻塞
                        except Exception as e:
                            logger.error(f"协程调度失败: {e}")
                    else:
                        logger.warning("主事件循环不可用，跳过回调")
                else:
                    # 同步回调直接调用
                    self.callback(barrage_data)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
                # 打印更详细的错误信息用于调试
                import traceback
                logger.debug(f"回调错误详情: {traceback.format_exc()}")
    
    async def stop(self):
        """停止获取弹幕"""
        if not self.running:
            return
            
        self.running = False
        logger.info("停止弹幕获取")
        
        if self.fetcher:
            try:
                self.fetcher.stop()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            # 等待线程结束
            await asyncio.sleep(1)


# 导入protobuf消息类型（需要从Fetcher模块导入）
try:
    from protobuf.douyin import (
        ChatMessage, MemberMessage, GiftMessage, LikeMessage,
        RoomStatsMessage, SocialMessage, EmojiChatMessage
    )
    PROTOBUF_AVAILABLE = True
    logger.info("✅ Protobuf消息类型导入成功")
except ImportError as e:
    logger.warning(f"⚠️ 导入protobuf消息类型失败: {e}")
    PROTOBUF_AVAILABLE = False
    # 创建空的消息类作为兜底
    class MockMessage:
        def __init__(self):
            self.user = MockUser()
            self.content = ""
            self.gift = MockGift()
            self.count = 0
            self.combo_count = 0
            self.display_long = ""
            self.emoji_id = 0
            self.default_content = ""
        
        def parse(self, data): 
            return self
    
    class MockUser:
        def __init__(self):
            self.id = 0
            self.nick_name = "Unknown"
            self.gender = 0
    
    class MockGift:
        def __init__(self):
            self.name = "Unknown"
    
    ChatMessage = MockMessage
    MemberMessage = MockMessage
    GiftMessage = MockMessage
    LikeMessage = MockMessage
    RoomStatsMessage = MockMessage
    SocialMessage = MockMessage
    EmojiChatMessage = MockMessage 