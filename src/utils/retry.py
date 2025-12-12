"""
可复用的重试装饰器
"""

import time
import logging
from typing import Callable, Type, Tuple, Optional, Any
from dataclasses import dataclass
from functools import wraps


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    delay: float = 2.0
    backoff_factor: float = 1.0  # 指数退避因子
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[int, Exception], None]] = None


def retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff_factor: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 指数退避因子，每次重试延迟乘以此因子
        exceptions: 需要捕获重试的异常类型
        on_retry: 重试时的回调函数，接收(attempt, exception)参数

    Returns:
        装饰器函数

    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        logger = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} 执行失败 "
                            f"(尝试 {attempt}/{max_attempts}): {e}"
                        )

                        if on_retry:
                            on_retry(attempt, e)

                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"{func.__name__} 最终失败 "
                            f"(共尝试 {max_attempts} 次): {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


def retry_with_config(config: RetryConfig):
    """
    使用配置对象的重试装饰器

    Args:
        config: 重试配置对象

    Returns:
        装饰器函数
    """
    return retry(
        max_attempts=config.max_attempts,
        delay=config.delay,
        backoff_factor=config.backoff_factor,
        exceptions=config.exceptions,
        on_retry=config.on_retry
    )
