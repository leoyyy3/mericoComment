"""
周报相关路由
"""

from flask import Blueprint, request, current_app, send_file
from pathlib import Path
from datetime import datetime
import tempfile
from src.utils import ResponseFormatter, LoggerFactory

weekly_bp = Blueprint('weekly', __name__)
logger = LoggerFactory.get_logger(__name__)

# 周报生成器实例（延迟初始化）
_report_generator = None


def _get_generator():
    """获取周报生成器实例"""
    global _report_generator

    if _report_generator is None:
        settings = current_app.config.get('SETTINGS')
        if settings:
            from src.services import WeeklyReportService
            _report_generator = WeeklyReportService(settings)

    return _report_generator


@weekly_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    生成周报

    POST /api/weekly-report/generate

    请求体:
    {
        "entity_id": "实体ID",
        "workspace_id": "工作空间ID",
        "custom_prompt": "自定义提示词（可选）",
        "save_to_file": true
    }
    """
    generator = _get_generator()

    if not generator:
        return ResponseFormatter.internal_error('周报服务未初始化')

    try:
        data = request.get_json()

        if not data:
            return ResponseFormatter.bad_request('请求体不能为空')

        entity_id = data.get('entity_id')
        workspace_id = data.get('workspace_id')
        custom_prompt = data.get('custom_prompt')
        save_to_file = data.get('save_to_file', True)

        if not entity_id or not workspace_id:
            return ResponseFormatter.bad_request('entity_id 和 workspace_id 是必需参数')

        logger.info(f"收到周报生成请求: entity_id={entity_id}, workspace_id={workspace_id}")

        # 生成周报
        result = generator.generate(
            entity_id=entity_id,
            workspace_id=workspace_id,
            custom_prompt=custom_prompt,
            save_to_file=save_to_file
        )

        return ResponseFormatter.success(result)

    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return ResponseFormatter.bad_request(f'参数错误: {str(e)}')

    except Exception as e:
        logger.error(f"生成周报失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'生成周报失败: {str(e)}')


@weekly_bp.route('/download', methods=['POST'])
def download_report():
    """
    生成并下载周报

    POST /api/weekly-report/download

    返回 Markdown 文件
    """
    generator = _get_generator()

    if not generator:
        return ResponseFormatter.internal_error('周报服务未初始化')

    try:
        data = request.get_json()

        if not data:
            return ResponseFormatter.bad_request('请求体不能为空')

        entity_id = data.get('entity_id')
        workspace_id = data.get('workspace_id')
        custom_prompt = data.get('custom_prompt')

        if not entity_id or not workspace_id:
            return ResponseFormatter.bad_request('entity_id 和 workspace_id 是必需参数')

        logger.info(f"收到周报下载请求: entity_id={entity_id}")

        # 生成到临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            result = generator.generate(
                entity_id=entity_id,
                workspace_id=workspace_id,
                custom_prompt=custom_prompt,
                save_to_file=False
            )
            tmp_file.write(result.get('report', ''))
            tmp_path = tmp_file.name

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f"weekly_report_{entity_id}_{timestamp}.md"

        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='text/markdown'
        )

    except Exception as e:
        logger.error(f"下载周报失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'下载周报失败: {str(e)}')


@weekly_bp.route('/list', methods=['GET'])
def list_reports():
    """
    列出所有周报

    GET /api/weekly-report/list
    """
    try:
        settings = current_app.config.get('SETTINGS')
        output_dir = Path(settings.output.output_dir if settings else 'output') / 'weekly_reports'

        if not output_dir.exists():
            return ResponseFormatter.success({
                'reports': [],
                'total': 0
            })

        reports = []
        files = sorted(output_dir.glob('weekly_report_*.md'), reverse=True)

        for file in files:
            stat = file.stat()
            reports.append({
                'name': file.name,
                'path': str(file),
                'size': f"{stat.st_size / 1024:.1f} KB",
                'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return ResponseFormatter.success({
            'reports': reports,
            'total': len(reports)
        })

    except Exception as e:
        logger.error(f"列出周报失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'列出周报失败: {str(e)}')


@weekly_bp.route('/find', methods=['GET'])
def find_report():
    """
    查找指定项目的周报

    GET /api/weekly-report/find?entity_id=xxx&latest=true
    """
    try:
        entity_id = request.args.get('entity_id')
        latest_only = request.args.get('latest', 'false').lower() == 'true'

        if not entity_id:
            return ResponseFormatter.bad_request('entity_id 是必需参数')

        settings = current_app.config.get('SETTINGS')
        output_dir = Path(settings.output.output_dir if settings else 'output') / 'weekly_reports'

        pattern = f"weekly_report_{entity_id}_*.md"
        files = sorted(output_dir.glob(pattern), reverse=True)

        if not files:
            return ResponseFormatter.success({
                'entity_id': entity_id,
                'reports': [],
                'total': 0
            })

        if latest_only:
            files = files[:1]

        reports = []
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()

                stat = file.stat()
                reports.append({
                    'file_name': file.name,
                    'file_path': str(file),
                    'content': content,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"读取文件失败 {file}: {e}")

        return ResponseFormatter.success({
            'entity_id': entity_id,
            'reports': reports,
            'total': len(reports)
        })

    except Exception as e:
        logger.error(f"查找周报失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'查找周报失败: {str(e)}')


@weekly_bp.route('/commits', methods=['POST'])
def get_commits():
    """
    获取提交记录

    POST /api/weekly-report/commits

    请求体:
    {
        "entity_id": "实体ID",
        "workspace_id": "工作空间ID"
    }
    """
    generator = _get_generator()

    if not generator:
        return ResponseFormatter.internal_error('周报服务未初始化')

    try:
        data = request.get_json()

        if not data:
            return ResponseFormatter.bad_request('请求体不能为空')

        entity_id = data.get('entity_id')
        workspace_id = data.get('workspace_id')

        if not entity_id or not workspace_id:
            return ResponseFormatter.bad_request('entity_id 和 workspace_id 是必需参数')

        commits = generator.get_commits(entity_id, workspace_id)

        return ResponseFormatter.success({
            'commits': commits,
            'total': len(commits)
        })

    except Exception as e:
        logger.error(f"获取提交记录失败: {e}", exc_info=True)
        return ResponseFormatter.internal_error(f'获取提交记录失败: {str(e)}')
