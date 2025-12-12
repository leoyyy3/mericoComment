"""
API 模块

统一的 RESTful API 服务，使用 Flask Blueprint 组织路由
"""

from .app import create_app
from .routes import health_bp, analysis_bp, weekly_bp

__all__ = ['create_app', 'health_bp', 'analysis_bp', 'weekly_bp']
