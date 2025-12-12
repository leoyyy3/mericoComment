"""
配置加载器

支持从 JSON 文件和环境变量加载配置
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .settings import (
    Settings,
    ServerConfig,
    MericoAPIConfig,
    ZhipuAIConfig,
    TAPDConfig,
    RequestConfig,
    OutputConfig,
    ScheduleConfig,
    init_settings
)

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    配置加载器

    支持:
    - JSON 配置文件
    - 环境变量覆盖
    - 多环境配置
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_file: 配置文件路径，默认为 config.json
        """
        self.config_file = Path(config_file) if config_file else Path('config.json')
        self._raw_config: Dict[str, Any] = {}

    def load(self) -> Settings:
        """
        加载配置

        Returns:
            Settings 配置对象
        """
        # 加载配置文件
        if self.config_file.exists():
            self._raw_config = self._load_json(self.config_file)
            logger.info(f"已加载配置文件: {self.config_file}")
        else:
            logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")

        # 构建配置对象
        settings = self._build_settings()

        # 设置全局配置
        init_settings(settings)

        return settings

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """加载 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _build_settings(self) -> Settings:
        """构建 Settings 对象"""
        # 服务器配置
        server_config = ServerConfig(
            host=self._get('server.host', '0.0.0.0'),
            port=int(self._get('server.port', 8080)),
            debug=self._get('server.debug', False)
        )

        # Merico API 配置
        merico_config = MericoAPIConfig(
            api_url=self._get('api_url', ''),
            duplicate_url=self._get('duplicate_url', ''),
            token=self._get('token', ''),
            repo_ids_file=self._get('repo_ids_file', 'repoIds_simple.json')
        )

        # 智谱 AI 配置
        zhipu_config = ZhipuAIConfig(
            api_key=self._get('zhipu_ai.api_key', ''),
            model=self._get('zhipu_ai.model', 'glm-4.5-flash')
        )

        # TAPD 配置
        tapd_cookies = self._get('tapd.cookies', {})
        tapd_config = TAPDConfig(
            base_url=self._get('tapd.base_url', 'https://www.tapd.cn/api/devops/source_code'),
            cookies=tapd_cookies if isinstance(tapd_cookies, dict) else {}
        )

        # 请求配置
        request_config = RequestConfig(
            timeout=int(self._get('request_settings.timeout', 30)),
            retry_times=int(self._get('request_settings.retry_times', 3)),
            retry_delay=float(self._get('request_settings.retry_delay', 2.0)),
            batch_delay=float(self._get('request_settings.batch_delay', 0.5)),
            page_size=int(self._get('request_settings.page_size', 100))
        )

        # 输出配置
        output_config = OutputConfig(
            output_dir=Path(self._get('output_settings.output_dir', 'output')),
            log_dir=Path(self._get('output_settings.log_dir', 'log')),
            save_classified=self._get('output_settings.save_classified', True),
            pretty_print=self._get('output_settings.pretty_print', True)
        )

        # 定时任务配置
        schedule_config = ScheduleConfig(
            enabled=self._get('schedule.enabled', True),
            hour=int(self._get('schedule.hour', 7)),
            minute=int(self._get('schedule.minute', 0))
        )

        return Settings(
            env=os.getenv('ENV', 'development'),
            server=server_config,
            merico=merico_config,
            zhipu_ai=zhipu_config,
            tapd=tapd_config,
            request=request_config,
            output=output_config,
            schedule=schedule_config
        )

    def _get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        支持点号分隔的嵌套键，如 'zhipu_ai.api_key'

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        # 首先检查环境变量
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # 从配置文件获取
        keys = key.split('.')
        value = self._raw_config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @staticmethod
    def create_template(output_path: str = 'config.json.template') -> None:
        """
        创建配置模板文件

        Args:
            output_path: 输出路径
        """
        template = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False
            },
            "api_url": "your-merico-api-url",
            "duplicate_url": "https://merico.idc.hexun.com/buffet/api/tech_debt/duplicated_group",
            "token": "your-merico-token",
            "repo_ids_file": "repoIds_simple.json",
            "zhipu_ai": {
                "api_key": "your-zhipu-api-key-here",
                "model": "glm-4.5-flash"
            },
            "tapd": {
                "base_url": "https://www.tapd.cn/api/devops/source_code",
                "cookies": {
                    "tapdsession": "your-session-here",
                    "t_u": "your-t-u-here"
                }
            },
            "request_settings": {
                "timeout": 30,
                "retry_times": 3,
                "retry_delay": 2.0,
                "batch_delay": 0.5,
                "page_size": 100
            },
            "output_settings": {
                "output_dir": "output",
                "log_dir": "log",
                "save_classified": True,
                "pretty_print": True
            },
            "schedule": {
                "enabled": True,
                "hour": 7,
                "minute": 0
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)

        logger.info(f"配置模板已创建: {output_path}")
