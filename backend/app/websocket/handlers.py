"""
WebSocket Handlers
WebSocket消息处理器
"""

import asyncio
import base64
import json
from typing import Optional

from .manager import manager, SessionState
from ..asr.whisper_engine import WhisperEngine
from ..translator.factory import get_translator
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 全局ASR引擎
_asr_engine: Optional[WhisperEngine] = None


def get_asr_engine() -> WhisperEngine:
    """获取ASR引擎（单例）"""
    global _asr_engine
    if _asr_engine is None:
        _asr_engine = WhisperEngine({
            "model_size": settings.WHISPER_MODEL,
            "device": settings.WHISPER_DEVICE
        })
    return _asr_engine


async def handle_audio(session_id: str, audio_base64: str):
    """处理音频数据"""
    try:
        # 解码base64
        audio_data = base64.b64decode(audio_base64)
        
        # 添加到缓冲区
        manager.add_audio(session_id, audio_data)
        
        # 更新状态
        manager.set_state(session_id, SessionState.LISTENING)
        
    except Exception as e:
        logger.error(f"Failed to handle audio for {session_id}: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "code": "AUDIO_ERROR",
            "message": str(e)
        })


async def handle_finalize(session_id: str):
    """处理语音结束，开始识别和翻译"""
    try:
        # 获取音频缓冲区
        audio_data = manager.get_audio_and_clear(session_id)
        
        if len(audio_data) < 1600:  # 至少0.1秒
            logger.debug(f"Audio too short for {session_id}: {len(audio_data)} bytes")
            return
        
        manager.set_state(session_id, SessionState.PROCESSING)
        
        # 发送处理状态
        await manager.send_message(session_id, {
            "type": "status",
            "status": "processing",
            "message": "正在识别..."
        })
        
        # 获取配置
        config = manager.get_config(session_id)
        source_lang = config.get("source_lang", "auto")
        target_lang = config.get("target_lang", "ZH")
        
        # ASR识别
        asr = get_asr_engine()
        asr_result = await asr.transcribe(
            audio_data,
            language=None if source_lang == "auto" else source_lang
        )
        
        original_text = asr_result.text.strip()
        detected_lang = asr_result.language
        
        if not original_text:
            logger.debug(f"No speech detected for {session_id}")
            manager.set_state(session_id, SessionState.IDLE)
            return
        
        # 发送识别结果
        await manager.send_message(session_id, {
            "type": "asr_result",
            "text": original_text,
            "language": detected_lang,
            "confidence": asr_result.confidence
        })
        
        # 翻译
        await manager.send_message(session_id, {
            "type": "status",
            "status": "translating",
            "message": "正在翻译..."
        })
        
        translator = get_translator()
        translation = await translator.translate(
            original_text,
            source=detected_lang,
            target=target_lang
        )
        
        # 发送翻译结果
        await manager.send_message(session_id, {
            "type": "result",
            "original_text": original_text,
            "translated_text": translation.translated_text,
            "source_lang": translation.source_lang,
            "target_lang": translation.target_lang,
            "provider": translation.provider,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        manager.set_state(session_id, SessionState.IDLE)
        
        logger.info(
            f"Session {session_id}: '{original_text[:20]}...' -> "
            f"'{translation.translated_text[:20]}...'"
        )
        
    except Exception as e:
        logger.error(f"Failed to finalize for {session_id}: {e}")
        manager.stats["errors"] += 1
        
        await manager.send_message(session_id, {
            "type": "error",
            "code": "PROCESSING_ERROR",
            "message": str(e)
        })
        
        manager.set_state(session_id, SessionState.ERROR)


async def handle_config(session_id: str, config: dict):
    """处理配置更新"""
    try:
        manager.update_config(session_id, config)
        
        await manager.send_message(session_id, {
            "type": "config_updated",
            "config": manager.get_config(session_id)
        })
        
        logger.debug(f"Session {session_id} config updated: {config}")
        
    except Exception as e:
        logger.error(f"Failed to update config for {session_id}: {e}")


async def handle_control(session_id: str, action: str):
    """处理控制命令"""
    try:
        if action == "start":
            manager.set_state(session_id, SessionState.LISTENING)
            manager.clear_audio_buffer(session_id)
            
            await manager.send_message(session_id, {
                "type": "status",
                "status": "listening",
                "message": "开始录音"
            })
            
        elif action == "stop":
            # 触发处理
            await handle_finalize(session_id)
            
        elif action == "clear":
            manager.clear_audio_buffer(session_id)
            manager.set_state(session_id, SessionState.IDLE)
            
            await manager.send_message(session_id, {
                "type": "status",
                "status": "idle",
                "message": "已清空"
            })
            
        else:
            logger.warning(f"Unknown control action: {action}")
            
    except Exception as e:
        logger.error(f"Failed to handle control for {session_id}: {e}")


async def dispatch_message(session_id: str, data: dict):
    """分发消息到对应处理器"""
    msg_type = data.get("type")
    
    if msg_type == "audio":
        audio_base64 = data.get("data", "")
        await handle_audio(session_id, audio_base64)
        
    elif msg_type == "config":
        config = data.get("config", {})
        await handle_config(session_id, config)
        
    elif msg_type == "control":
        action = data.get("action", "")
        await handle_control(session_id, action)
        
    elif msg_type == "finalize":
        await handle_finalize(session_id)
        
    elif msg_type == "ping":
        await manager.send_message(session_id, {"type": "pong"})
        
    else:
        logger.warning(f"Unknown message type: {msg_type}")
