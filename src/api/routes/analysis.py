"""
代码分析相关路由

包含:
- 未注释函数分析
- 重复函数分析
"""

from flask import Blueprint, request, current_app, send_from_directory
from pathlib import Path
from datetime import datetime
from src.utils import ResponseFormatter, LoggerFactory

analysis_bp = Blueprint('analysis', __name__)
logger = LoggerFactory.get_logger(__name__)


@analysis_bp.route('/uncommented/run', methods=['POST'])
def run_uncommented_analysis():
    """
    运行未注释函数分析

    POST /api/analysis/uncommented/run

    响应:
    {
        "success": true,
        "message": "分析任务已完成",
        "data": {
            "report_file": "报告文件路径"
        }
    }
    """
    try:
        logger.info("开始执行未注释函数分析...")

        settings = current_app.config.get('SETTINGS')

        # 动态导入避免循环依赖
        from src.services import AnalysisService
        service = AnalysisService(settings)
        result = service.run_uncommented_analysis()

        logger.info("未注释函数分析完成")

        return ResponseFormatter.success(
            data=result,
            message='未注释函数分析完成'
        )

    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        return ResponseFormatter.bad_request(f'配置文件不存在: {str(e)}')

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'分析失败: {str(e)}')


@analysis_bp.route('/duplicate/run', methods=['POST'])
def run_duplicate_analysis():
    """
    运行重复函数分析

    POST /api/analysis/duplicate/run
    """
    try:
        logger.info("开始执行重复函数分析...")

        settings = current_app.config.get('SETTINGS')

        from src.services import AnalysisService
        service = AnalysisService(settings)
        result = service.run_duplicate_analysis()

        logger.info("重复函数分析完成")

        return ResponseFormatter.success(
            data=result,
            message='重复函数分析完成'
        )

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'分析失败: {str(e)}')


@analysis_bp.route('/all/run', methods=['POST'])
def run_all_analysis():
    """
    运行所有分析

    POST /api/analysis/all/run
    """
    try:
        logger.info("开始执行完整分析...")

        settings = current_app.config.get('SETTINGS')

        from src.services import AnalysisService
        service = AnalysisService(settings)
        result = service.run_all()

        logger.info("完整分析完成")

        return ResponseFormatter.success(
            data=result,
            message='完整分析完成'
        )

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'分析失败: {str(e)}')


@analysis_bp.route('/reports', methods=['GET'])
def list_reports():
    """
    列出所有分析报告

    GET /api/analysis/reports
    GET /api/analysis/reports?type=uncommented
    GET /api/analysis/reports?type=duplicate
    """
    try:
        settings = current_app.config.get('SETTINGS')
        output_dir = settings.output.output_dir if settings else Path('output')

        report_type = request.args.get('type', 'all')

        reports = []
        patterns = []

        if report_type in ['all', 'uncommented']:
            patterns.append('uncommented_functions_report*.html')

        if report_type in ['all', 'duplicate']:
            patterns.append('duplicate_functions_report_*.html')

        for pattern in patterns:
            files = sorted(output_dir.glob(pattern), reverse=True)
            for file in files:
                if 'latest' in file.name:
                    continue
                stat = file.stat()
                reports.append({
                    'name': file.name,
                    'type': 'duplicate' if 'duplicate' in file.name else 'uncommented',
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'url': f'/api/analysis/reports/{file.name}'
                })

        # 按时间排序
        reports.sort(key=lambda x: x['created_at'], reverse=True)

        return ResponseFormatter.success({
            'reports': reports,
            'total': len(reports)
        })

    except Exception as e:
        logger.error(f"获取报告列表失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'获取报告列表失败: {str(e)}')


@analysis_bp.route('/reports/<path:filename>', methods=['GET'])
def download_report(filename: str):
    """
    下载分析报告

    GET /api/analysis/reports/<filename>
    """
    settings = current_app.config.get('SETTINGS')
    output_dir = settings.output.output_dir if settings else Path('output')

    return send_from_directory(output_dir, filename)
