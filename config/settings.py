"""
配置设置类

使用 dataclass 定义类型安全的配置
支持从环境变量和配置文件加载
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from pathlib import Path


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = '0.0.0.0'
    port: int = 8080
    debug: bool = False


@dataclass
class MericoAPIConfig:
    """Merico API 配置"""
    api_url: str = ''
    duplicate_url: str = ''  # 重复函数 API URL
    token: str = ''
    repo_ids_file: str = 'repoIds_simple.json'


@dataclass
class ZhipuAIConfig:
    """智谱 AI 配置"""
    api_key: str = ''
    model: str = 'glm-4.5-flash'


@dataclass
class TAPDConfig:
    """TAPD 配置"""
    base_url: str = 'https://www.tapd.cn/api/devops/source_code'
    cookies: Dict[str, str] = field(default_factory=dict)


@dataclass
class RequestConfig:
    """请求配置"""
    timeout: int = 30
    retry_times: int = 3
    retry_delay: float = 2.0
    batch_delay: float = 0.5
    page_size: int = 100


@dataclass
class OutputConfig:
    """输出配置"""
    output_dir: Path = field(default_factory=lambda: Path('output'))
    log_dir: Path = field(default_factory=lambda: Path('log'))
    save_classified: bool = True
    pretty_print: bool = True


@dataclass
class ScheduleConfig:
    """定时任务配置"""
    enabled: bool = True
    hour: int = 7
    minute: int = 0


@dataclass
class Settings:
    """
    统一配置管理

    优先级：环境变量 > 配置文件 > 默认值
    """
    # 环境标识
    env: str = 'development'

    # 各模块配置
    server: ServerConfig = field(default_factory=ServerConfig)
    merico: MericoAPIConfig = field(default_factory=MericoAPIConfig)
    zhipu_ai: ZhipuAIConfig = field(default_factory=ZhipuAIConfig)
    tapd: TAPDConfig = field(default_factory=TAPDConfig)
    request: RequestConfig = field(default_factory=RequestConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)

    def __post_init__(self):
        """从环境变量加载敏感配置"""
        self._load_from_env()
        self._ensure_directories()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 环境
        self.env = os.getenv('ENV', self.env)

        # 服务器配置
        self.server.host = os.getenv('SERVER_HOST', self.server.host)
        self.server.port = int(os.getenv('SERVER_PORT', self.server.port))
        self.server.debug = os.getenv('DEBUG', '').lower() == 'true'

        # Merico API
        self.merico.token = os.getenv('MERICO_TOKEN', self.merico.token)
        self.merico.api_url = os.getenv('MERICO_API_URL', self.merico.api_url)
        self.merico.duplicate_url = os.getenv('MERICO_DUPLICATE_URL', self.merico.duplicate_url)

        # 智谱 AI
        self.zhipu_ai.api_key = os.getenv('ZHIPU_API_KEY', self.zhipu_ai.api_key)
        self.zhipu_ai.model = os.getenv('ZHIPU_MODEL', self.zhipu_ai.model)

        # TAPD（Cookies 从配置文件加载）
        self.tapd.base_url = os.getenv('TAPD_BASE_URL', self.tapd.base_url)

    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.output.output_dir.mkdir(exist_ok=True)
        self.output.log_dir.mkdir(exist_ok=True)

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env == 'production'

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env == 'development'

    def to_dict(self) -> Dict:
        """转换为字典（用于兼容旧代码）"""
        return {
            'env': self.env,
            'token': self.merico.token,
            'api_url': self.merico.api_url,
            'duplicate_url': self.merico.duplicate_url,
            'repo_ids_file': self.merico.repo_ids_file,
            'zhipu_ai': {
                'api_key': self.zhipu_ai.api_key,
                'model': self.zhipu_ai.model
            },
            'tapd': {
                'base_url': self.tapd.base_url,
                'cookies': self.tapd.cookies
            },
            'request_settings': {
                'timeout': self.request.timeout,
                'retry_times': self.request.retry_times,
                'retry_delay': self.request.retry_delay,
                'batch_delay': self.request.batch_delay,
                'page_size': self.request.page_size
            },
            'output_settings': {
                'output_dir': str(self.output.output_dir),
                'log_dir': str(self.output.log_dir),
                'save_classified': self.output.save_classified,
                'pretty_print': self.output.pretty_print
            },
        }


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def init_settings(settings: Settings) -> None:
    """初始化全局配置"""
    global _settings
    _settings = settings
