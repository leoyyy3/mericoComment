"""
统一日志配置工厂
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerFactory:
    """
    日志工厂类

    提供统一的日志配置和管理
    """

    # 默认配置
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_LOG_DIR = Path('log')

    _initialized = False

    @classmethod
    def setup(
        cls,
        level: int = logging.INFO,
        log_dir: Optional[Path] = None,
        log_file_prefix: str = 'app',
        console_output: bool = True,
        file_output: bool = True,
        format_string: Optional[str] = None
    ) -> None:
        """
        配置全局日志

        Args:
            level: 日志级别
            log_dir: 日志目录
            log_file_prefix: 日志文件前缀
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            format_string: 自定义格式字符串
        """
        if cls._initialized:
            return

        log_dir = log_dir or cls.DEFAULT_LOG_DIR
        log_dir.mkdir(exist_ok=True)

        handlers = []

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            handlers.append(console_handler)

        # 文件处理器
        if file_output:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = log_dir / f'{log_file_prefix}_{timestamp}.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            handlers.append(file_handler)

        # 配置根日志器
        logging.basicConfig(
            level=level,
            format=format_string or cls.DEFAULT_FORMAT,
            datefmt=cls.DEFAULT_DATE_FORMAT,
            handlers=handlers
        )

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取日志器

        Args:
            name: 日志器名称，通常使用 __name__

        Returns:
            日志器实例
        """
        if not cls._initialized:
            cls.setup()

        return logging.getLogger(name)

    @classmethod
    def reset(cls) -> None:
        """重置日志配置（主要用于测试）"""
        cls._initialized = False

        # 移除所有处理器
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
