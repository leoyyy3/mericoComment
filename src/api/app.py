"""
Flask 应用工厂

使用工厂模式创建 Flask 应用，支持不同配置
"""

from flask import Flask
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ConfigLoader, get_settings
from src.utils import LoggerFactory


def create_app(config_file: str = None) -> Flask:
    """
    创建 Flask 应用

    Args:
        config_file: 配置文件路径

    Returns:
        Flask 应用实例
    """
    # 加载配置
    loader = ConfigLoader(config_file)
    settings = loader.load()

    # 初始化日志
    LoggerFactory.setup(
        log_dir=settings.output.log_dir,
        log_file_prefix='api',
        console_output=True,
        file_output=True
    )

    logger = LoggerFactory.get_logger(__name__)
    logger.info(f"正在创建应用，环境: {settings.env}")

    # 创建 Flask 应用
    app = Flask(
        __name__,
        template_folder=str(project_root / 'templates'),
        static_folder=str(project_root / 'output')
    )

    # 配置应用
    app.config['DEBUG'] = settings.server.debug
    app.config['SETTINGS'] = settings

    # 注册蓝图
    _register_blueprints(app)

    # 注册错误处理器
    _register_error_handlers(app)

    # 初始化定时任务
    if settings.schedule.enabled:
        _init_scheduler(app, settings)

    logger.info("应用创建完成")

    return app


def _register_blueprints(app: Flask) -> None:
    """注册所有蓝图"""
    from .routes import health_bp, analysis_bp, weekly_bp, web_bp

    # 健康检查 API
    app.register_blueprint(health_bp, url_prefix='/api')

    # 代码分析 API
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')

    # 周报 API
    app.register_blueprint(weekly_bp, url_prefix='/api/weekly-report')

    # Web 页面
    app.register_blueprint(web_bp)


def _register_error_handlers(app: Flask) -> None:
    """注册错误处理器"""
    from src.utils import ResponseFormatter

    @app.errorhandler(400)
    def bad_request(error):
        return ResponseFormatter.bad_request(str(error))

    @app.errorhandler(404)
    def not_found(error):
        return ResponseFormatter.not_found()

    @app.errorhandler(500)
    def internal_error(error):
        return ResponseFormatter.internal_error()


def _init_scheduler(app: Flask, settings) -> None:
    """初始化定时任务"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    logger = LoggerFactory.get_logger(__name__)

    scheduler = BackgroundScheduler()

    # 每日分析任务
    scheduler.add_job(
        func=_run_daily_analysis,
        trigger=CronTrigger(
            hour=settings.schedule.hour,
            minute=settings.schedule.minute
        ),
        id='daily_analysis',
        name='每日代码质量分析',
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        f"定时任务已配置: 每天 {settings.schedule.hour:02d}:{settings.schedule.minute:02d} 运行"
    )

    # 存储到 app 上下文
    app.scheduler = scheduler


def _run_daily_analysis():
    """执行每日分析任务"""
    logger = LoggerFactory.get_logger(__name__)
    logger.info("开始执行每日分析任务...")

    try:
        # 这里调用分析服务
        from src.services import AnalysisService
        service = AnalysisService()
        service.run_all()
        logger.info("每日分析任务完成")
    except Exception as e:
        logger.error(f"每日分析任务失败: {e}", exc_info=True)
