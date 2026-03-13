"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import Literal, List, Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Voice Translator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Whisper ASR
    WHISPER_MODEL: str = "tiny"  # tiny, base, small, medium
    WHISPER_DEVICE: str = "cpu"  # cpu, cuda
    
    # Translator (支持切换)
    TRANSLATOR_PROVIDER: Literal["deeplx", "google", "baidu", "youdao"] = "deeplx"
    
    # DeepLX
    DEEPLX_ENDPOINT: str = "https://api.deeplx.org/translate"
    DEEPLX_TIMEOUT: int = 10
    
    # Google Translate
    GOOGLE_API_KEY: str = ""
    
    # Baidu Translate
    BAIDU_APP_ID: str = ""
    BAIDU_SECRET_KEY: str = ""
    
    # Youdao Translate
    YOUDAO_APP_KEY: str = ""
    YOUDAO_SECRET_KEY: str = ""
    
    # Fallback
    TRANSLATOR_FALLBACK_ENABLED: bool = True
    
    @property
    def TRANSLATOR_FALLBACK_ORDER(self) -> List[str]:
        return ["google", "baidu"]
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    
    # Audio
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    AUDIO_CHUNK_MS: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
