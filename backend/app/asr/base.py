"""
ASR base module
语音识别基类
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ASRResult:
    """语音识别结果"""
    text: str
    language: str
    confidence: float = 1.0
    is_final: bool = True
    segments: Optional[List[Dict]] = None
    metadata: Optional[Dict[str, Any]] = None


class ASRError(Exception):
    """ASR错误"""
    pass


class BaseASR(ABC):
    """ASR基类"""
    
    PROVIDER_NAME: str = "base"
    SUPPORTED_LANGUAGES: list = []
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> ASRResult:
        """
        转录音频
        
        Args:
            audio_data: PCM音频数据 (16kHz, 16bit, mono)
            language: 语言代码（None为自动检测）
        
        Returns:
            ASRResult: 识别结果
        """
        pass
    
    @abstractmethod
    async def detect_language(self, audio_data: bytes) -> str:
        """检测语言"""
        pass
