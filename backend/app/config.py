"""
Configuration management
"""

from pydantic_settings import BaseSettings
from typing import Literal, List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Voice Translator"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Whisper
    WHISPER_MODEL: str = "tiny"
    WHISPER_DEVICE: str = "cpu"
    
    # Translator (support switching)
    TRANSLATOR_PROVIDER: Literal["deeplx", "google", "baidu", "youdao"] = "deeplx"
    
    # DeepLX
    DEEPLX_ENDPOINT: str = "https://api.deeplx.org/translate"
    DEEPLX_TIMEOUT: int = 10
    
    # Google
    GOOGLE_API_KEY: str = ""
    
    # Baidu
    BAIDU_APP_ID: str = ""
    BAIDU_SECRET_KEY: str = ""
    
    # Youdao
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
    AUDIO_CHUNK_MS: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
