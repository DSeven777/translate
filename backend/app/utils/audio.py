"""
Audio utility functions
音频处理工具
"""

import numpy as np
from typing import Tuple


def pcm_to_float(pcm_data: bytes, dtype: np.dtype = np.float32) -> np.ndarray:
    """
    PCM转float格式
    
    Args:
        pcm_data: 16bit PCM数据
        dtype: 目标类型
    
    Returns:
        numpy数组
    """
    audio = np.frombuffer(pcm_data, dtype=np.int16)
    return audio.astype(dtype) / 32768.0


def float_to_pcm(audio: np.ndarray) -> bytes:
    """
    float转PCM格式
    
    Args:
        audio: float音频数组
    
    Returns:
        PCM bytes
    """
    # 裁剪到[-1, 1]
    audio = np.clip(audio, -1.0, 1.0)
    # 转换为int16
    pcm = (audio * 32767).astype(np.int16)
    return pcm.tobytes()


def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    重采样（简单实现）
    
    Args:
        audio: 音频数组
        orig_sr: 原始采样率
        target_sr: 目标采样率
    
    Returns:
        重采样后的音频
    """
    if orig_sr == target_sr:
        return audio
    
    ratio = target_sr / orig_sr
    n_samples = int(len(audio) * ratio)
    
    # 简单线性插值
    indices = np.linspace(0, len(audio) - 1, n_samples)
    return np.interp(indices, np.arange(len(audio)), audio)


def calculate_energy(audio: np.ndarray) -> float:
    """
    计算音频能量
    
    Args:
        audio: 音频数组
    
    Returns:
        能量值
    """
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))


def split_audio_by_silence(
    audio: np.ndarray,
    sample_rate: int = 16000,
    min_silence_ms: int = 500,
    energy_threshold: float = 0.01
) -> list:
    """
    按静音分割音频
    
    Args:
        audio: 音频数组
        sample_rate: 采样率
        min_silence_ms: 最小静音时长（毫秒）
        energy_threshold: 能量阈值
    
    Returns:
        音频片段列表
    """
    min_silence_samples = int(min_silence_ms * sample_rate / 1000)
    chunk_size = int(sample_rate * 0.1)  # 100ms chunks
    
    segments = []
    current_segment = []
    silence_count = 0
    
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        energy = calculate_energy(chunk)
        
        if energy < energy_threshold:
            silence_count += len(chunk)
            if silence_count >= min_silence_samples and current_segment:
                # 输出当前段落
                segments.append(np.concatenate(current_segment))
                current_segment = []
        else:
            silence_count = 0
            current_segment.append(chunk)
    
    # 处理最后一段
    if current_segment:
        segments.append(np.concatenate(current_segment))
    
    return segments
