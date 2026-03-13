"""
Whisper ASR Engine
语音识别引擎
"""

import numpy as np
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .base import BaseASR, ASRResult, ASRError
from .vad import SimpleVAD, VADConfig
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 线程池用于异步执行Whisper
_executor = ThreadPoolExecutor(max_workers=2)


class WhisperEngine(BaseASR):
    """Whisper ASR引擎"""
    
    PROVIDER_NAME = "whisper"
    
    # Whisper支持的语言
    SUPPORTED_LANGUAGES = [
        "zh", "en", "ja", "ko", "fr", "de", "es", "pt", "it", "ru",
        "ar", "hi", "th", "vi", "nl", "pl", "tr", "uk", "sv", "id"
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        
        self.model_size = self.config.get("model_size", settings.WHISPER_MODEL)
        self.device = self.config.get("device", settings.WHISPER_DEVICE)
        
        # VAD
        vad_config = VADConfig(
            energy_threshold=self.config.get("vad_energy_threshold", 0.01),
            silence_duration_ms=self.config.get("vad_silence_ms", 500),
        )
        self.vad = SimpleVAD(vad_config)
        
        # 模型延迟加载
        self._model = None
        self._is_loaded = False
        
        logger.info(f"WhisperEngine: model={self.model_size}, device={self.device}")
    
    def _load_model(self):
        """加载模型"""
        if self._is_loaded:
            return
        
        logger.info(f"Loading Whisper model: {self.model_size}...")
        try:
            import whisper
            self._model = whisper.load_model(
                self.model_size,
                device=self.device
            )
            self._is_loaded = True
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise ASRError(f"Failed to load Whisper model: {e}")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> ASRResult:
        """
        转录音频
        
        Args:
            audio_data: PCM音频数据 (16kHz, 16bit, mono)
            language: 语言代码
        
        Returns:
            ASRResult: 识别结果
        """
        # 确保模型加载
        self._load_model()
        
        # 检查音频有效性
        if not audio_data or len(audio_data) < 1600:  # 至少0.1秒
            return ASRResult(
                text="",
                language=language or "unknown",
                confidence=0.0,
                is_final=True
            )
        
        # 转换为numpy数组
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        
        # 转换为float32（Whisper期望）
        audio_float = audio_np.astype(np.float32) / 32768.0
        
        try:
            # 在线程池中执行（Whisper是同步的）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                self._transcribe_sync,
                audio_float,
                language
            )
            return result
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise ASRError(f"Transcription failed: {e}")
    
    def _transcribe_sync(
        self,
        audio: np.ndarray,
        language: Optional[str]
    ) -> ASRResult:
        """同步转录（在线程池中执行）"""
        result = self._model.transcribe(
            audio,
            language=language,
            task="transcribe",
            fp16=False if self.device == "cpu" else True,
            verbose=False
        )
        
        text = result.get("text", "").strip()
        detected_lang = result.get("language", language or "unknown")
        
        # 计算置信度
        segments = result.get("segments", [])
        if segments:
            avg_logprob = np.mean([s.get("avg_logprob", 0) for s in segments])
            confidence = float(np.exp(avg_logprob))
        else:
            confidence = 1.0
        
        logger.debug(f"Whisper: '{text[:30]}...' (lang={detected_lang}, conf={confidence:.2f})")
        
        return ASRResult(
            text=text,
            language=detected_lang,
            confidence=confidence,
            is_final=True,
            segments=segments,
            metadata={"raw_result": result}
        )
    
    async def detect_language(self, audio_data: bytes) -> str:
        """检测语言"""
        result = await self.transcribe(audio_data, language=None)
        return result.language
    
    def reset_vad(self):
        """重置VAD状态"""
        self.vad.reset()
    
    def process_vad(self, audio_chunk: np.ndarray) -> tuple:
        """
        VAD处理
        
        Returns:
            (should_finalize, is_speech)
        """
        return self.vad.process(audio_chunk)
    
    @property
    def is_loaded(self) -> bool:
        """模型是否已加载"""
        return self._is_loaded
