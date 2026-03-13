"""
WebSocket Connection Manager
WebSocket连接管理器
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional
from collections import defaultdict
import time
import asyncio
import json

from ..utils.logger import get_logger
from ..config import settings

logger = get_logger(__name__)


class SessionState:
    """会话状态"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 会话配置
        self.session_configs: Dict[str, dict] = {}
        
        # 会话状态
        self.session_states: Dict[str, str] = {}
        
        # 音频缓冲区
        self.audio_buffers: Dict[str, bytearray] = defaultdict(bytearray)
        
        # 统计
        self.stats = {
            "total_connections": 0,
            "total_messages": 0,
            "errors": 0,
        }
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """接受新连接"""
        await websocket.accept()
        
        self.active_connections[session_id] = websocket
        self.session_states[session_id] = SessionState.IDLE
        self.session_configs[session_id] = {
            "source_lang": "auto",
            "target_lang": "ZH"
        }
        
        self.stats["total_connections"] += 1
        
        logger.info(
            f"WebSocket connected: {session_id}. "
            f"Active: {len(self.active_connections)}"
        )
        
        # 发送欢迎消息
        await self.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to Voice Translator"
        })
    
    def disconnect(self, session_id: str):
        """断开连接"""
        self.active_connections.pop(session_id, None)
        self.session_configs.pop(session_id, None)
        self.session_states.pop(session_id, None)
        self.audio_buffers.pop(session_id, None)
        
        logger.info(
            f"WebSocket disconnected: {session_id}. "
            f"Active: {len(self.active_connections)}"
        )
    
    async def send_message(self, session_id: str, message: dict):
        """发送消息"""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(message)
                self.stats["total_messages"] += 1
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
    
    async def broadcast(self, message: dict):
        """广播消息"""
        for session_id in list(self.active_connections.keys()):
            await self.send_message(session_id, message)
    
    def update_config(self, session_id: str, config: dict):
        """更新会话配置"""
        if session_id in self.session_configs:
            self.session_configs[session_id].update(config)
            logger.debug(f"Session {session_id} config updated: {config}")
    
    def get_config(self, session_id: str) -> dict:
        """获取会话配置"""
        return self.session_configs.get(session_id, {
            "source_lang": "auto",
            "target_lang": "ZH"
        })
    
    def set_state(self, session_id: str, state: str):
        """设置会话状态"""
        self.session_states[session_id] = state
    
    def get_state(self, session_id: str) -> str:
        """获取会话状态"""
        return self.session_states.get(session_id, SessionState.IDLE)
    
    def add_audio(self, session_id: str, audio_data: bytes):
        """添加音频数据到缓冲区"""
        self.audio_buffers[session_id].extend(audio_data)
    
    def get_audio_buffer(self, session_id: str) -> bytearray:
        """获取音频缓冲区"""
        return self.audio_buffers[session_id]
    
    def clear_audio_buffer(self, session_id: str):
        """清空音频缓冲区"""
        self.audio_buffers[session_id] = bytearray()
    
    def get_audio_and_clear(self, session_id: str) -> bytes:
        """获取并清空音频缓冲区"""
        buffer = self.audio_buffers[session_id]
        audio_data = bytes(buffer)
        buffer.clear()
        return audio_data
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            "active_connections": len(self.active_connections),
            "sessions": list(self.active_connections.keys())
        }


# 全局连接管理器
manager = ConnectionManager()
