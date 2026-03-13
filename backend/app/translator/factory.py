"""
Translator Factory - Support runtime switching
"""

from typing import Dict, Type, List, Optional
from .base import BaseTranslator, TranslatorError
from .deeplx import DeepLXTranslator
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TranslatorFactory:
    _translators: Dict[str, Type[BaseTranslator]] = {}
    _instances: Dict[str, BaseTranslator] = {}
    
    @classmethod
    def _init(cls):
        if cls._translators:
            return
        cls._translators["deeplx"] = DeepLXTranslator
        # TODO: Add google, baidu, youdao when implemented
    
    @classmethod
    def create(cls, provider: str, config: Optional[Dict] = None) -> BaseTranslator:
        cls._init()
        
        if provider not in cls._translators:
            raise ValueError(f"Unsupported: {provider}. Available: {list(cls._translators.keys())}")
        
        if provider in cls._instances:
            return cls._instances[provider]
        
        translator_class = cls._translators[provider]
        config = config or cls._get_config(provider)
        instance = translator_class(config)
        cls._instances[provider] = instance
        logger.info(f"Created translator: {provider}")
        return instance
    
    @classmethod
    def _get_config(cls, provider: str) -> Dict:
        configs = {
            "deeplx": {
                "endpoint": settings.DEEPLX_ENDPOINT,
                "timeout": settings.DEEPLX_TIMEOUT,
            },
        }
        return configs.get(provider, {})
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        cls._init()
        return list(cls._translators.keys())


class TranslatorManager:
    """Support auto-fallback"""
    
    def __init__(
        self,
        primary: str,
        fallbacks: Optional[List[str]] = None,
        auto_fallback: bool = True
    ):
        self.primary = primary
        self.fallbacks = fallbacks or []
        self.auto_fallback = auto_fallback
        
        self._current = TranslatorFactory.create(primary)
        self._current_name = primary
        
        logger.info(f"TranslatorManager: primary={primary}, fallbacks={fallbacks}")
    
    async def translate(self, text: str, source: str = "auto", target: str = "en"):
        try:
            return await self._current.translate(text, source, target)
        except TranslatorError as e:
            if not self.auto_fallback:
                raise
            
            logger.warning(f"Primary translator failed: {e}")
            
            for name in self.fallbacks:
                try:
                    t = TranslatorFactory.create(name)
                    result = await t.translate(text, source, target)
                    self._current = t
                    self._current_name = name
                    logger.info(f"Switched to fallback: {name}")
                    return result
                except TranslatorError:
                    continue
            
            raise TranslatorError("All translators failed")
    
    @property
    def current_provider(self) -> str:
        return self._current_name


# Global instance
_manager: Optional[TranslatorManager] = None


def get_translator() -> TranslatorManager:
    global _manager
    if _manager is None:
        _manager = TranslatorManager(
            primary=settings.TRANSLATOR_PROVIDER,
            fallbacks=settings.TRANSLATOR_FALLBACK_ORDER if settings.TRANSLATOR_FALLBACK_ENABLED else [],
            auto_fallback=settings.TRANSLATOR_FALLBACK_ENABLED
        )
    return _manager
