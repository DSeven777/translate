"""
VAD (Voice Activity Detection)
语音活动检测 - 简单能量检测实现
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class VADConfig:
    """VAD配置"""
    energy_threshold: float = 0.01
    silence_duration_ms: int = 500
    min_speech_duration_ms: int = 300
    sample_rate: int = 16000


class SimpleVAD:
    """简单的能量检测VAD"""
    
    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self.silence_samples = int(
            self.config.silence_duration_ms * self.config.sample_rate / 1000
        )
        self.min_speech_samples = int(
            self.config.min_speech_duration_ms * self.config.sample_rate / 1000
        )
        self.reset()
    
    def reset(self):
        """重置状态"""
        self.silent_chunks = 0
        self.speech_samples = 0
        self.is_speaking = False
    
    def is_silence(self, audio: np.ndarray) -> bool:
        """检测是否为静音"""
        if len(audio) == 0:
            return True
        energy = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
        return energy < self.config.energy_threshold
    
    def process(self, audio_chunk: np.ndarray) -> tuple:
        """
        处理音频块
        
        Args:
            audio_chunk: int16 PCM音频块
        
        Returns:
            (should_finalize, is_speech)
            - should_finalize: 是否应该输出当前句子
            - is_speech: 当前是否在说话
        """
        is_silence = self.is_silence(audio_chunk)
        
        if is_silence:
            self.silent_chunks += len(audio_chunk)
            
            # 静音持续时间超过阈值，且之前有足够的语音
            if (self.silent_chunks >= self.silence_samples and 
                self.speech_samples >= self.min_speech_samples):
                return True, False
        else:
            self.silent_chunks = 0
            self.speech_samples += len(audio_chunk)
            self.is_speaking = True
        
        return False, not is_silence
    
    def get_speech_buffer(self) -> int:
        """获取当前语音缓冲区大小（采样数）"""
        return self.speech_samples
