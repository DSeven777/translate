"""
Models - Request/Response schemas
数据模型
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ConfigRequest(BaseModel):
    """配置请求"""
    source_lang: str = "auto"
    target_lang: str = "ZH"


class TranslationRequest(BaseModel):
    """翻译请求（REST API备用）"""
    text: str
    source_lang: str = "auto"
    target_lang: str = "ZH"


class TranslationResponse(BaseModel):
    """翻译响应"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    confidence: Optional[float] = None


class ASRResponse(BaseModel):
    """ASR响应"""
    text: str
    language: str
    confidence: float
    is_final: bool = True


class WSMessage(BaseModel):
    """WebSocket消息"""
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    whisper_loaded: bool
    translator: str
    active_sessions: int


class ErrorResponse(BaseModel):
    """错误响应"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
