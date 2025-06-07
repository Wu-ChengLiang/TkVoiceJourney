#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块
提供弹幕数据分析、用户行为分析、AI效果分析等功能
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)


class DataAnalytics:
    """数据分析类"""
    
    def __init__(self):
        self.barrage_history: List[Dict] = []
        self.ai_response_history: List[Dict] = []
        self.user_activity: Dict[str, Any] = defaultdict(dict)
        self.hourly_stats: Dict[str, Any] = defaultdict(dict)
        
    def add_barrage(self, barrage_data: Dict):
        """添加弹幕数据"""
        try:
            # 添加时间戳
            if 'timestamp' not in barrage_data:
                barrage_data['timestamp'] = time.time()
            
            self.barrage_history.append(barrage_data)
            
            # 更新用户活动统计
            self._update_user_activity(barrage_data)
            
            # 更新小时统计
            self._update_hourly_stats(barrage_data)
            
            # 保持历史记录在合理范围内
            if len(self.barrage_history) > 10000:
                self.barrage_history = self.barrage_history[-8000:]
                
        except Exception as e:
            logger.error(f"添加弹幕数据失败: {e}")
    
    def add_ai_response(self, response_data: Dict):
        """添加AI回复数据"""
        try:
            if 'timestamp' not in response_data:
                response_data['timestamp'] = time.time()
                
            self.ai_response_history.append(response_data)
            
            # 保持历史记录在合理范围内
            if len(self.ai_response_history) > 1000:
                self.ai_response_history = self.ai_response_history[-800:]
                
        except Exception as e:
            logger.error(f"添加AI回复数据失败: {e}")
    
    def _update_user_activity(self, barrage_data: Dict):
        """更新用户活动统计"""
        try:
            user_id = barrage_data.get('user_id', 'unknown')
            username = barrage_data.get('username', 'unknown')
            
            if user_id not in self.user_activity:
                self.user_activity[user_id] = {
                    'username': username,
                    'message_count': 0,
                    'first_seen': barrage_data['timestamp'],
                    'last_seen': barrage_data['timestamp'],
                    'message_types': defaultdict(int),
                    'total_chars': 0
                }
            
            user_stats = self.user_activity[user_id]
            user_stats['message_count'] += 1
            user_stats['last_seen'] = barrage_data['timestamp']
            user_stats['message_types'][barrage_data.get('type', 'unknown')] += 1
            
            # 统计字符数（仅聊天消息）
            if barrage_data.get('type') == 'chat':
                content = barrage_data.get('content', '')
                user_stats['total_chars'] += len(content)
                
        except Exception as e:
            logger.error(f"更新用户活动统计失败: {e}")
    
    def _update_hourly_stats(self, barrage_data: Dict):
        """更新小时统计"""
        try:
            timestamp = barrage_data['timestamp']
            hour_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:00')
            
            if hour_key not in self.hourly_stats:
                self.hourly_stats[hour_key] = {
                    'total_messages': 0,
                    'unique_users': set(),
                    'message_types': defaultdict(int),
                    'avg_message_length': 0,
                    'total_chars': 0
                }
            
            hour_stats = self.hourly_stats[hour_key]
            hour_stats['total_messages'] += 1
            hour_stats['unique_users'].add(barrage_data.get('user_id', 'unknown'))
            hour_stats['message_types'][barrage_data.get('type', 'unknown')] += 1
            
            # 统计消息长度
            if barrage_data.get('type') == 'chat':
                content = barrage_data.get('content', '')
                hour_stats['total_chars'] += len(content)
                if hour_stats['total_messages'] > 0:
                    hour_stats['avg_message_length'] = hour_stats['total_chars'] / hour_stats['total_messages']
                    
        except Exception as e:
            logger.error(f"更新小时统计失败: {e}")
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """获取实时统计数据"""
        try:
            current_time = time.time()
            last_5min = current_time - 300  # 5分钟
            last_1hour = current_time - 3600  # 1小时
            
            # 最近5分钟的数据
            recent_barrages = [
                b for b in self.barrage_history 
                if b.get('timestamp', 0) >= last_5min
            ]
            
            # 最近1小时的数据
            hourly_barrages = [
                b for b in self.barrage_history 
                if b.get('timestamp', 0) >= last_1hour
            ]
            
            # 消息类型统计
            msg_types_5min = Counter(b.get('type', 'unknown') for b in recent_barrages)
            msg_types_1hour = Counter(b.get('type', 'unknown') for b in hourly_barrages)
            
            # 活跃用户统计
            active_users_5min = len(set(b.get('user_id', 'unknown') for b in recent_barrages))
            active_users_1hour = len(set(b.get('user_id', 'unknown') for b in hourly_barrages))
            
            # AI回复统计
            recent_ai_responses = [
                r for r in self.ai_response_history 
                if r.get('timestamp', 0) >= last_1hour
            ]
            
            return {
                'realtime': {
                    'total_messages_5min': len(recent_barrages),
                    'total_messages_1hour': len(hourly_barrages),
                    'active_users_5min': active_users_5min,
                    'active_users_1hour': active_users_1hour,
                    'message_types_5min': dict(msg_types_5min),
                    'message_types_1hour': dict(msg_types_1hour),
                    'ai_responses_1hour': len(recent_ai_responses),
                    'last_update': current_time
                }
            }
            
        except Exception as e:
            logger.error(f"获取实时统计失败: {e}")
            return {'realtime': {}}
    
    def get_user_analysis(self, limit: int = 20) -> Dict[str, Any]:
        """获取用户分析数据"""
        try:
            # 按消息数量排序用户
            top_users = sorted(
                self.user_activity.items(),
                key=lambda x: x[1]['message_count'],
                reverse=True
            )[:limit]
            
            # 活跃度分析
            current_time = time.time()
            active_threshold = current_time - 3600  # 1小时内活跃
            
            active_users = [
                (user_id, stats) for user_id, stats in self.user_activity.items()
                if stats['last_seen'] >= active_threshold
            ]
            
            # 用户类型分析
            user_types = {
                'chatters': 0,    # 聊天用户
                'lurkers': 0,     # 潜水用户
                'gifters': 0,     # 送礼用户
                'supporters': 0   # 点赞用户
            }
            
            for user_id, stats in self.user_activity.items():
                msg_types = stats['message_types']
                if msg_types.get('chat', 0) > 0:
                    user_types['chatters'] += 1
                if msg_types.get('gift', 0) > 0:
                    user_types['gifters'] += 1
                if msg_types.get('like', 0) > 0:
                    user_types['supporters'] += 1
                if sum(msg_types.values()) <= 1:
                    user_types['lurkers'] += 1
            
            return {
                'user_analysis': {
                    'total_users': len(self.user_activity),
                    'active_users_1hour': len(active_users),
                    'top_users': [
                        {
                            'user_id': user_id,
                            'username': stats['username'],
                            'message_count': stats['message_count'],
                            'total_chars': stats['total_chars'],
                            'message_types': dict(stats['message_types'])
                        }
                        for user_id, stats in top_users
                    ],
                    'user_types': user_types
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户分析失败: {e}")
            return {'user_analysis': {}}
    
    def get_ai_performance(self) -> Dict[str, Any]:
        """获取AI性能分析"""
        try:
            if not self.ai_response_history:
                return {'ai_performance': {'total_responses': 0}}
            
            current_time = time.time()
            last_24hours = current_time - 86400  # 24小时
            
            # 最近24小时的AI回复
            recent_responses = [
                r for r in self.ai_response_history 
                if r.get('timestamp', 0) >= last_24hours
            ]
            
            # 按小时分组统计
            hourly_responses = defaultdict(int)
            for response in recent_responses:
                hour = datetime.fromtimestamp(response['timestamp']).strftime('%H:00')
                hourly_responses[hour] += 1
            
            # 回复效果分析（基于源弹幕数量）
            total_source_barrages = 0
            for response in recent_responses:
                source_barrages = response.get('source_barrages', [])
                total_source_barrages += len(source_barrages)
            
            avg_response_time = 8  # 固定8秒间隔
            
            return {
                'ai_performance': {
                    'total_responses': len(self.ai_response_history),
                    'responses_24h': len(recent_responses),
                    'avg_response_time': avg_response_time,
                    'total_source_barrages': total_source_barrages,
                    'hourly_distribution': dict(hourly_responses),
                    'response_efficiency': len(recent_responses) / max(total_source_barrages, 1) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"获取AI性能分析失败: {e}")
            return {'ai_performance': {}}
    
    def get_trend_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """获取趋势分析"""
        try:
            current_time = time.time()
            start_time = current_time - (hours * 3600)
            
            # 按小时分组
            hourly_data = defaultdict(lambda: {
                'messages': 0,
                'users': set(),
                'types': defaultdict(int)
            })
            
            for barrage in self.barrage_history:
                timestamp = barrage.get('timestamp', 0)
                if timestamp >= start_time:
                    hour_key = datetime.fromtimestamp(timestamp).strftime('%m-%d %H:00')
                    hourly_data[hour_key]['messages'] += 1
                    hourly_data[hour_key]['users'].add(barrage.get('user_id', 'unknown'))
                    hourly_data[hour_key]['types'][barrage.get('type', 'unknown')] += 1
            
            # 转换为时间序列数据
            trend_data = []
            for hour_key in sorted(hourly_data.keys()):
                data = hourly_data[hour_key]
                trend_data.append({
                    'time': hour_key,
                    'messages': data['messages'],
                    'users': len(data['users']),
                    'types': dict(data['types'])
                })
            
            return {
                'trend_analysis': {
                    'time_range': f'{hours}小时',
                    'data': trend_data,
                    'peak_hour': max(trend_data, key=lambda x: x['messages'])['time'] if trend_data else None,
                    'total_hours': len(trend_data)
                }
            }
            
        except Exception as e:
            logger.error(f"获取趋势分析失败: {e}")
            return {'trend_analysis': {}}
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """获取综合报告"""
        try:
            current_time = time.time()
            last_5min = current_time - 300
            last_1hour = current_time - 3600
            
            # 实时数据
            recent_barrages = [b for b in self.barrage_history if b.get('timestamp', 0) >= last_5min]
            hourly_barrages = [b for b in self.barrage_history if b.get('timestamp', 0) >= last_1hour]
            
            # 消息类型统计
            msg_types = Counter(b.get('type', 'unknown') for b in recent_barrages)
            
            # 活跃用户
            active_users = len(set(b.get('user_id', 'unknown') for b in hourly_barrages))
            
            # AI回复统计
            recent_ai = [r for r in self.ai_response_history if r.get('timestamp', 0) >= last_1hour]
            
            return {
                'summary': {
                    'total_barrages': len(self.barrage_history),
                    'total_ai_responses': len(self.ai_response_history),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'realtime': {
                    'messages_5min': len(recent_barrages),
                    'messages_1hour': len(hourly_barrages),
                    'active_users_1hour': active_users,
                    'message_types': dict(msg_types),
                    'ai_responses_1hour': len(recent_ai)
                }
            }
            
        except Exception as e:
            logger.error(f"获取综合报告失败: {e}")
            return {'error': str(e)}
    
    def export_data(self, filepath: str = None) -> str:
        """导出数据到JSON文件"""
        try:
            if not filepath:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filepath = f"data_export_{timestamp}.json"
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'barrage_history': self.barrage_history,
                'ai_response_history': self.ai_response_history,
                'user_activity': {
                    user_id: {
                        **stats,
                        'message_types': dict(stats['message_types'])
                    }
                    for user_id, stats in self.user_activity.items()
                },
                'statistics': self.get_comprehensive_report()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据导出成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            return None


# 全局数据分析实例
analytics = DataAnalytics() 