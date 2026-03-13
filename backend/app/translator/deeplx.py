"""
DeepLX Translator - Free DeepL API
"""

import httpx
from typing import Dict, Any, Optional
from .base import BaseTranslator, TranslationResult, TranslatorError, TranslatorErrorCode


class DeepLXTranslator(BaseTranslator):
    PROVIDER_NAME = "deeplx"
    
    LANG_MAP = {
        "zh": "ZH", "zh-cn": "ZH", "zh-tw": "ZH",
        "en": "EN", "en-us": "EN", "en-gb": "EN",
        "ja": "JA", "jp": "JA",
        "ko": "KO", "kr": "KO",
        "fr": "FR", "de": "DE", "es": "ES",
        "pt": "PT", "it": "IT", "ru": "RU",
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.deeplx.org/translate")
        self.timeout = config.get("timeout", 10)
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "ZH"
    ) -> TranslationResult:
        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.PROVIDER_NAME
            )
        
        source_lang = self._normalize_lang(source_lang)
        target_lang = self._normalize_lang(target_lang)
        
        try:
            response = await self.client.post(
                self.endpoint,
                json={
                    "text": text,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 200:
                raise TranslatorError(f"DeepLX error: {data}")
            
            return TranslationResult(
                original_text=text,
                translated_text=data.get("data", text),
                source_lang=data.get("source_lang", source_lang),
                target_lang=target_lang,
                provider=self.PROVIDER_NAME,
                metadata={"raw_response": data}
            )
        
        except httpx.TimeoutException:
            raise TranslatorError("Timeout", TranslatorErrorCode.TIMEOUT)
        except httpx.HTTPStatusError as e:
            raise TranslatorError(f"HTTP {e.response.status_code}", TranslatorErrorCode.NETWORK_ERROR)
        except Exception as e:
            raise TranslatorError(str(e))
    
    async def detect_language(self, text: str) -> str:
        result = await self.translate(text, "auto", "ZH")
        return result.source_lang
    
    def _normalize_lang(self, lang: str) -> str:
        if lang == "auto":
            return "auto"
        return self.LANG_MAP.get(lang.lower(), lang.upper())
    
    async def close(self):
        await self.client.aclose()
