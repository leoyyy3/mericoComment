"""
健康检查路由
"""

from flask import Blueprint, current_app
from datetime import datetime
from src.utils import ResponseFormatter

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口

    GET /api/health

    响应:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "merico-analysis-api",
            "timestamp": "2025-01-01T00:00:00",
            "version": "2.0.0",
            "env": "development"
        }
    }
    """
    settings = current_app.config.get('SETTINGS')

    return ResponseFormatter.success({
        'status': 'healthy',
        'service': 'merico-analysis-api',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'env': settings.env if settings else 'unknown'
    })


@health_bp.route('/status', methods=['GET'])
def service_status():
    """
    服务状态接口

    GET /api/status

    返回更详细的服务状态信息
    """
    settings = current_app.config.get('SETTINGS')
    scheduler = getattr(current_app, 'scheduler', None)

    # 获取定时任务信息
    jobs = []
    if scheduler:
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })

    return ResponseFormatter.success({
        'status': 'running',
        'env': settings.env if settings else 'unknown',
        'scheduled_jobs': jobs,
        'timestamp': datetime.now().isoformat()
    })
