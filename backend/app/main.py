"""
Voice Translator Backend
Main FastAPI Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from .config import settings
from .utils.logger import get_logger
from .websocket.manager import manager
from .websocket.handlers import dispatch_message
from .translator.factory import get_translator
from .asr.whisper_engine import WhisperEngine
from .models import (
    TranslationRequest, TranslationResponse,
    HealthResponse, ErrorResponse
)

logger = get_logger(__name__)

# 全局ASR引擎
_asr_engine = None


def get_asr_engine():
    global _asr_engine
    if _asr_engine is None:
        _asr_engine = WhisperEngine({
            "model_size": settings.WHISPER_MODEL,
            "device": settings.WHISPER_DEVICE
        })
    return _asr_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Translator: {settings.TRANSLATOR_PROVIDER}")
    logger.info(f"Whisper: {settings.WHISPER_MODEL} on {settings.WHISPER_DEVICE}")
    
    # 预加载Whisper模型
    logger.info("Pre-loading Whisper model...")
    engine = get_asr_engine()
    engine._load_model()
    logger.info("Whisper model loaded")
    
    yield
    
    # 关闭时
    logger.info("Shutting down...")


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ REST API ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    asr = get_asr_engine()
    translator = get_translator()
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        whisper_loaded=asr.is_loaded,
        translator=translator.current_provider,
        active_sessions=len(manager.active_connections)
    )


@app.get("/languages")
async def get_languages():
    """获取支持的语言"""
    return {
        "asr": [
            {"code": "zh", "name": "中文"},
            {"code": "en", "name": "英语"},
            {"code": "ja", "name": "日语"},
            {"code": "ko", "name": "韩语"},
            {"code": "fr", "name": "法语"},
            {"code": "de", "name": "德语"},
            {"code": "es", "name": "西班牙语"},
            {"code": "auto", "name": "自动检测"}
        ],
        "translation": [
            {"code": "ZH", "name": "中文"},
            {"code": "EN", "name": "英语"},
            {"code": "JA", "name": "日语"},
            {"code": "KO", "name": "韩语"},
            {"code": "FR", "name": "法语"},
            {"code": "DE", "name": "德语"},
            {"code": "ES", "name": "西班牙语"},
        ]
    }


@app.post("/api/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """翻译文本（REST API备用）"""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    
    try:
        translator = get_translator()
        result = await translator.translate(
            request.text,
            source=request.source_lang,
            target=request.target_lang
        )
        
        return TranslationResponse(
            original_text=result.original_text,
            translated_text=result.translated_text,
            source_lang=result.source_lang,
            target_lang=result.target_lang,
            provider=result.provider,
            confidence=result.confidence
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    return manager.get_stats()


# ============ WebSocket ============

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket端点"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 分发处理
            await dispatch_message(session_id, data)
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
        
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        
    finally:
        manager.disconnect(session_id)


# ============ Error Handlers ============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal Server Error",
        "detail": str(exc) if settings.DEBUG else "An error occurred"
    }
