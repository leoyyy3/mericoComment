'''
Author: leoyang liuyang2020@staff.hexun.com
Date: 2025-12-10 15:59:43
LastEditors: leoyang liuyang2020@staff.hexun.com
LastEditTime: 2025-12-10 16:30:31
Description: 
'''
"""
Web 页面路由
"""

from flask import Blueprint, render_template, current_app, send_from_directory
from pathlib import Path
from datetime import datetime
from src.utils import LoggerFactory

web_bp = Blueprint('web', __name__)
logger = LoggerFactory.get_logger(__name__)


@web_bp.route('/')
def index():
    """首页"""
    settings = current_app.config.get('SETTINGS')

    schedule_time = "07:00"
    if settings and settings.schedule:
        schedule_time = f"{settings.schedule.hour:02d}:{settings.schedule.minute:02d}"

    return render_template('web/index.html', schedule_time=schedule_time)


@web_bp.route('/duplicate-functions')
def duplicate_functions_page():
    """重复函数分析页面"""
    reports = _get_reports('duplicate_functions_report_*.html', 'duplicate_functions_report_latest.html')

    return render_template(
        'web/report_list.html',
        title='重复函数分析报告',
        icon='🔄',
        reports=reports
    )


@web_bp.route('/uncommented-functions')
def uncommented_functions_page():
    """未注释函数分析页面"""
    reports = _get_reports('uncommented_functions_report*.html')

    return render_template(
        'web/report_list.html',
        title='未注释函数分析报告',
        icon='📝',
        reports=reports
    )


@web_bp.route('/output/<path:filename>')
def serve_report(filename: str):
    """提供报告文件访问"""
    settings = current_app.config.get('SETTINGS')
    output_dir = settings.output.output_dir if settings else Path('output')

    return send_from_directory(output_dir, filename)


def _get_reports(pattern: str, exclude: str = None) -> list:
    """获取报告列表"""
    settings = current_app.config.get('SETTINGS')
    output_dir = settings.output.output_dir if settings else Path('output')

    reports = []
    files = sorted(output_dir.glob(pattern), reverse=True)

    for file in files:
        if exclude and file.name == exclude:
            continue

        stat = file.stat()
        reports.append({
            'name': file.name,
            'size': f"{stat.st_size / 1024:.1f} KB",
            'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'url': f'/output/{file.name}'
        })

    return reports
