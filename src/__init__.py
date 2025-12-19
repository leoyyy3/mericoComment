"""
Merico 代码质量分析系统
"""

__version__ = "2.0.0"

from .tasks.connection import get_redis_connection

__all__ = [
    "__version__",
    "get_redis_connection",
]
