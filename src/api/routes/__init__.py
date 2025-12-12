"""
API 路由模块

使用 Flask Blueprint 组织各个功能模块的路由
"""

from .health import health_bp
from .analysis import analysis_bp
from .weekly import weekly_bp
from .web import web_bp

__all__ = ['health_bp', 'analysis_bp', 'weekly_bp', 'web_bp']
