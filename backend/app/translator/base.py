"""
Translator base class
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class TranslatorErrorCode(Enum):
    UNKNOWN = "UNKNOWN"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    AUTH_FAILED = "AUTH_FAILED"
    NETWORK_ERROR = "NETWORK_ERROR"


class TranslatorError(Exception):
    def __init__(self, message: str, code: TranslatorErrorCode = TranslatorErrorCode.UNKNOWN):
        self.message = message
        self.code = code
        super().__init__(self.message)


@dataclass
class TranslationResult:
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTranslator(ABC):
    PROVIDER_NAME: str = "base"
    SUPPORTED_LANGUAGES: list = []
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._is_available: Optional[bool] = None
    
    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en"
    ) -> TranslationResult:
        pass
    
    async def health_check(self) -> bool:
        try:
            await self.translate("hello", "en", "zh")
            self._is_available = True
            return True
        except Exception:
            self._is_available = False
            return False
    
    @property
    def is_available(self) -> Optional[bool]:
        return self._is_available
