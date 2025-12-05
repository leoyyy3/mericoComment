"""
统一的代码质量分析Web服务
整合重复函数分析和函数注释分析两个功能
"""

from flask import Flask, render_template, send_from_directory, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import os
import json

# 导入分析模块
from fetch_duplicate_functions import DuplicateFunctionsFetcher
from display_duplicate_functions import DuplicateFunctionsDisplay
from merico_agent_advanced import MericoUncommentedFunctionsAgent

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Web服务配置"""
    # 路径配置
    OUTPUT_DIR = Path("output")
    CONFIG_FILE = Path("config.json")
    
    # 服务配置
    DEFAULT_PORT = 8080
    HOST = '0.0.0.0'
    DEBUG = False
    
    # 定时任务配置
    SCHEDULE_HOUR = 7
    SCHEDULE_MINUTE = 0
    
    # 报告文件模式
    DUPLICATE_REPORT_PATTERN = "duplicate_functions_report_*.html"
    UNCOMMENTED_REPORT_PATTERN = "uncommented_functions_report*.html"


# 确保输出目录存在
Config.OUTPUT_DIR.mkdir(exist_ok=True)

# 定时任务调度器
scheduler = BackgroundScheduler()


def get_reports(pattern: str, exclude: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    获取报告文件列表
    
    Args:
        pattern: 文件匹配模式
        exclude: 要排除的文件名
        
    Returns:
        报告信息列表
    """
    reports = []
    files = sorted(Config.OUTPUT_DIR.glob(pattern), reverse=True)
    
    for file in files:
        if exclude and file.name == exclude:
            continue
            
        stat = file.stat()
        reports.append({
            'name': file.name,
            'size': f"{stat.st_size / 1024:.1f} KB",
            'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'url': f'/reports/{file.name}'
        })
    
    return reports


def run_duplicate_analysis() -> None:
    """执行重复函数分析"""
    try:
        logger.info("开始执行重复函数分析...")
        fetcher = DuplicateFunctionsFetcher()
        fetcher.run()
        logger.info("✅ 重复函数分析完成!")
        
        # 创建最新报告链接
        html_files = sorted(Config.OUTPUT_DIR.glob(Config.DUPLICATE_REPORT_PATTERN))
        if html_files:
            latest = html_files[-1]
            latest_link = Config.OUTPUT_DIR / "duplicate_functions_report_latest.html"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(latest.name)
            
    except Exception as e:
        logger.error(f"❌ 重复函数分析失败: {e}", exc_info=True)


def run_uncommented_analysis() -> None:
    """执行未注释函数分析"""
    try:
        logger.info("开始执行未注释函数分析...")
        
        # 检查配置文件
        if not Config.CONFIG_FILE.exists():
            logger.error(f"配置文件不存在: {Config.CONFIG_FILE}")
            raise FileNotFoundError(f"配置文件不存在: {Config.CONFIG_FILE}")
        
        # 加载配置
        with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 执行分析
        agent = MericoUncommentedFunctionsAgent(config)
        agent.run()
        
        logger.info("✅ 未注释函数分析完成!")
        
    except FileNotFoundError as e:
        logger.error(f"❌ 配置文件错误: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 未注释函数分析失败: {e}", exc_info=True)
        raise


def run_all_analysis() -> None:
    """执行所有分析"""
    logger.info("开始执行完整分析...")
    run_duplicate_analysis()
    run_uncommented_analysis()
    logger.info("✅ 完整分析完成!")


@app.route('/')
def index() -> str:
    """首页 - 显示功能导航"""
    schedule_time = f"{Config.SCHEDULE_HOUR:02d}:{Config.SCHEDULE_MINUTE:02d}"
    return render_template('web/index.html', schedule_time=schedule_time)


@app.route('/duplicate-functions')
def duplicate_functions_page() -> str:
    """重复函数分析页面"""
    reports = get_reports(
        Config.DUPLICATE_REPORT_PATTERN,
        exclude="duplicate_functions_report_latest.html"
    )
    return render_template(
        'web/report_list.html',
        title='重复函数分析报告',
        icon='🔄',
        reports=reports
    )


@app.route('/uncommented-functions')
def uncommented_functions_page() -> str:
    """未注释函数分析页面"""
    reports = get_reports(Config.UNCOMMENTED_REPORT_PATTERN)
    print(reports)
    return render_template(
        'web/report_list.html',
        title='未注释函数分析报告',
        icon='📝',
        reports=reports
    )


@app.route('/reports/<path:filename>')
def serve_report(filename: str):
    """提供报告文件访问"""
    return send_from_directory(Config.OUTPUT_DIR, filename)


@app.route('/api/status')
def api_status() -> Dict[str, Any]:
    """API: 获取服务状态"""
    # 重复函数报告
    duplicate_files = list(Config.OUTPUT_DIR.glob(Config.DUPLICATE_REPORT_PATTERN))
    latest_duplicate = None
    if duplicate_files:
        latest = max(duplicate_files, key=lambda p: p.stat().st_mtime)
        latest_duplicate = {
            'name': latest.name,
            'mtime': datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
            'size': latest.stat().st_size
        }
    
    # 未注释函数报告
    uncommented_files = list(Config.OUTPUT_DIR.glob(Config.UNCOMMENTED_REPORT_PATTERN))
    latest_uncommented = None
    if uncommented_files:
        latest = max(uncommented_files, key=lambda p: p.stat().st_mtime)
        latest_uncommented = {
            'name': latest.name,
            'mtime': datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
            'size': latest.stat().st_size
        }
    
    # 定时任务信息
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return jsonify({
        'status': 'running',
        'duplicate_analysis': {
            'latest_report': latest_duplicate,
            'total_reports': len(duplicate_files)
        },
        'uncommented_analysis': {
            'latest_report': latest_uncommented,
            'total_reports': len(uncommented_files)
        },
        'scheduled_jobs': jobs
    })


@app.route('/api/run-analysis/<analysis_type>', methods=['POST'])
def api_run_analysis(analysis_type: str):
    """API: 手动触发分析"""
    try:
        if analysis_type == 'duplicate':
            run_duplicate_analysis()
        elif analysis_type == 'uncommented':
            run_uncommented_analysis()
        elif analysis_type == 'all':
            run_all_analysis()
        else:
            return jsonify({
                'success': False,
                'error': f'无效的分析类型: {analysis_type}'
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'{analysis_type} 分析完成'
        })
        
    except FileNotFoundError as e:
        logger.error(f"配置文件错误: {e}")
        return jsonify({
            'success': False,
            'error': f'配置文件不存在: {str(e)}'
        }), 500
        
    except Exception as e:
        logger.error(f"API触发分析失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def init_scheduler() -> None:
    """初始化定时任务"""
    # 每天早上7:00运行完整分析
    scheduler.add_job(
        func=run_all_analysis,
        trigger=CronTrigger(hour=Config.SCHEDULE_HOUR, minute=Config.SCHEDULE_MINUTE),
        id='daily_analysis',
        name='每日代码质量分析',
        replace_existing=True
    )
    
    logger.info(
        f"✅ 定时任务已配置: 每天 {Config.SCHEDULE_HOUR:02d}:{Config.SCHEDULE_MINUTE:02d} 运行完整分析"
    )
    scheduler.start()
    logger.info("✅ 调度器已启动")


if __name__ == '__main__':
    # 初始化定时任务
    init_scheduler()
    
    # 启动Flask应用
    port = int(os.environ.get('PORT', Config.DEFAULT_PORT))
    logger.info(f"🚀 启动代码质量分析Web服务,监听端口 {port}")
    
    app.run(host=Config.HOST, port=port, debug=Config.DEBUG)
