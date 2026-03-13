"""
Logger utility
"""

import logging
import sys
from typing import Optional

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    获取Logger实例
    
    Args:
        name: Logger名称
        level: 日志级别
    
    Returns:
        Logger实例
    """
    logger = logging.getLogger(name or "voice_translator")
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
        )
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger
