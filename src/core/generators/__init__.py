"""
生成器模块
"""

from .weekly_generator import (
    TAPDClient,
    ZhipuAIClient,
    WeeklyReportGenerator
)

__all__ = [
    'TAPDClient',
    'ZhipuAIClient',
    'WeeklyReportGenerator'
]
