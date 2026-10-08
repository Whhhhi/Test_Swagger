"""
日志模块 — 基于 Loguru 的全局日志封装

特性:
- 自动轮转（按天/大小）
- 同时输出到文件和控制台
- 支持上下文绑定（request_id, 用例名等）
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_level: str = "DEBUG", log_retention: str = "7 days") -> logger:
    """配置并返回全局 logger 实例

    Args:
        log_level: 日志级别
        log_retention: 日志文件保留时长

    Returns:
        配置好的 logger 对象
    """
    # 避免重复添加 handler
    logger.remove()

    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "petstore_{time:YYYY-MM-DD}.log"

    # 文件输出 — 带完整调试信息
    logger.add(
        sink=str(log_file),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {extra[request_id]:>6} | {name}:{function}:{line} | {message}",
        rotation="00:00",       # 每日 0 点轮转
        retention=log_retention,
        compression="gz",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    # 控制台输出 — 简洁风格
    logger.add(
        sink=sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{message}</cyan>",
        colorize=True,
        enqueue=True,
    )

    # 设置默认上下文
    logger.configure(extra={"request_id": "N/A"})

    return logger


# 全局共享实例
log = setup_logger()


def bind_logger(**kwargs) -> logger:
    """返回绑定上下文后的 logger"""
    return logger.bind(**kwargs)
