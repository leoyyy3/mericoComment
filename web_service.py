"""
统一的代码质量分析Web服务
整合重复函数分析和函数注释分析两个功能
"""

from flask import Flask, render_template, send_from_directory, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pathlib import Path
from datetime import datetime
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

# 配置路径
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# 定时任务调度器
scheduler = BackgroundScheduler()


def run_duplicate_analysis():
    """执行重复函数分析"""
    try:
        logger.info("开始执行重复函数分析...")
        fetcher = DuplicateFunctionsFetcher()
        fetcher.run()
        logger.info("✅ 重复函数分析完成!")
        
        # 创建最新报告链接
        html_files = sorted(OUTPUT_DIR.glob("duplicate_functions_report_*.html"))
        if html_files:
            latest = html_files[-1]
            latest_link = OUTPUT_DIR / "duplicate_functions_report_latest.html"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(latest.name)
            
    except Exception as e:
        logger.error(f"❌ 重复函数分析失败: {e}", exc_info=True)


def run_uncommented_analysis():
    """执行未注释函数分析"""
    try:
        logger.info("开始执行未注释函数分析...")
        
        # 加载配置
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 执行分析
        agent = MericoUncommentedFunctionsAgent(config)
        agent.run()
        
        logger.info("✅ 未注释函数分析完成!")
        
    except Exception as e:
        logger.error(f"❌ 未注释函数分析失败: {e}", exc_info=True)


def run_all_analysis():
    """执行所有分析"""
    logger.info("开始执行完整分析...")
    run_duplicate_analysis()
    run_uncommented_analysis()
    logger.info("✅ 完整分析完成!")


@app.route('/')
def index():
    """首页 - 显示功能导航"""
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Merico 代码质量分析平台</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                color: white;
                padding: 60px 20px;
            }
            .header h1 {
                font-size: 3em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 30px;
                margin-top: 40px;
            }
            .feature-card {
                background: white;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                transition: transform 0.3s;
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
            .feature-icon {
                font-size: 3em;
                margin-bottom: 20px;
            }
            .feature-card h2 {
                color: #333;
                margin-bottom: 15px;
            }
            .feature-card p {
                color: #666;
                margin-bottom: 25px;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                font-size: 16px;
                transition: background 0.3s;
                margin-right: 10px;
            }
            .btn:hover {
                background: #5568d3;
            }
            .btn-secondary {
                background: #6c757d;
            }
            .btn-secondary:hover {
                background: #5a6268;
            }
            .actions {
                background: white;
                border-radius: 12px;
                padding: 30px;
                margin-top: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
            }
            .actions h3 {
                margin-bottom: 20px;
                color: #333;
            }
            .status {
                display: inline-block;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                background: #d4edda;
                color: #155724;
                margin-left: 15px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Merico 代码质量分析平台</h1>
                <p>智能化代码质量分析与可视化</p>
            </div>
            
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">🔄</div>
                    <h2>重复函数分析</h2>
                    <p>检测代码库中的重复函数,帮助识别可重构的代码,提高代码复用率。</p>
                    <a href="/duplicate-functions" class="btn">查看报告</a>
                    <button class="btn btn-secondary" onclick="runAnalysis('duplicate')">立即分析</button>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📝</div>
                    <h2>函数注释分析</h2>
                    <p>分析函数注释覆盖率,识别缺少文档的函数,提升代码可维护性。</p>
                    <a href="/uncommented-functions" class="btn">查看报告</a>
                    <button class="btn btn-secondary" onclick="runAnalysis('uncommented')">立即分析</button>
                </div>
            </div>
            
            <div class="actions">
                <h3>全局操作</h3>
                <button class="btn" onclick="runAnalysis('all')" style="background: #28a745;">▶️ 运行完整分析</button>
                <a href="/api/status" class="btn btn-secondary">📊 查看状态</a>
                <span class="status">定时任务: 每天 7:00</span>
            </div>
        </div>
        
        <script>
            async function runAnalysis(type) {
                const messages = {
                    'duplicate': '重复函数分析',
                    'uncommented': '未注释函数分析',
                    'all': '完整分析'
                };
                
                if (!confirm(`确定要运行${messages[type]}吗?这可能需要几分钟时间。`)) {
                    return;
                }
                
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = '⏳ 分析中...';
                
                try {
                    const response = await fetch(`/api/run-analysis/${type}`, { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert(`✅ ${messages[type]}完成!`);
                        location.reload();
                    } else {
                        alert('❌ 分析失败: ' + data.error);
                    }
                } catch (error) {
                    alert('❌ 请求失败: ' + error.message);
                } finally {
                    btn.disabled = false;
                    btn.textContent = '立即分析';
                }
            }
        </script>
    </body>
    </html>
    """
    return html


@app.route('/duplicate-functions')
def duplicate_functions_page():
    """重复函数分析页面"""
    reports = []
    for file in sorted(OUTPUT_DIR.glob("duplicate_functions_report_*.html"), reverse=True):
        if file.name != "duplicate_functions_report_latest.html":
            stat = file.stat()
            reports.append({
                'name': file.name,
                'size': f"{stat.st_size / 1024:.1f} KB",
                'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'url': f'/reports/{file.name}'
            })
    
    return render_duplicate_list(reports)


@app.route('/uncommented-functions')
def uncommented_functions_page():
    """未注释函数分析页面"""
    reports = []
    for file in sorted(OUTPUT_DIR.glob("uncommented_functions_report*.html"), reverse=True):
        stat = file.stat()
        reports.append({
            'name': file.name,
            'size': f"{stat.st_size / 1024:.1f} KB",
            'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'url': f'/reports/{file.name}'
        })
    
    return render_uncommented_list(reports)


def render_duplicate_list(reports):
    """渲染重复函数报告列表"""
    table_rows = ""
    if reports:
        for report in reports:
            table_rows += f"""
            <tr>
                <td><a href="{report['url']}" class="report-link" target="_blank">{report['name']}</a></td>
                <td>{report['mtime']}</td>
                <td>{report['size']}</td>
            </tr>
            """
    else:
        table_rows = '<tr><td colspan="3" style="text-align:center;padding:40px;color:#999;">暂无报告,请运行分析</td></tr>'
    
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>重复函数分析报告</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }}
            h1 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #667eea; color: white; padding: 15px; text-align: left; }}
            td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
            tr:hover {{ background: #f8f9fa; }}
            .report-link {{ color: #667eea; text-decoration: none; }}
            .report-link:hover {{ text-decoration: underline; }}
            .back-btn {{ display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← 返回首页</a>
            <h1>🔄 重复函数分析报告</h1>
            <table>
                <thead>
                    <tr><th>报告名称</th><th>生成时间</th><th>文件大小</th></tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
    </body>
    </html>
    """


def render_uncommented_list(reports):
    """渲染未注释函数报告列表"""
    table_rows = ""
    if reports:
        for report in reports:
            table_rows += f"""
            <tr>
                <td><a href="{report['url']}" class="report-link" target="_blank">{report['name']}</a></td>
                <td>{report['mtime']}</td>
                <td>{report['size']}</td>
            </tr>
            """
    else:
        table_rows = '<tr><td colspan="3" style="text-align:center;padding:40px;color:#999;">暂无报告,请运行分析</td></tr>'
    
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>未注释函数分析报告</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }}
            h1 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #667eea; color: white; padding: 15px; text-align: left; }}
            td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
            tr:hover {{ background: #f8f9fa; }}
            .report-link {{ color: #667eea; text-decoration: none; }}
            .report-link:hover {{ text-decoration: underline; }}
            .back-btn {{ display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← 返回首页</a>
            <h1>📝 未注释函数分析报告</h1>
            <table>
                <thead>
                    <tr><th>报告名称</th><th>生成时间</th><th>文件大小</th></tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
    </body>
    </html>
    """


@app.route('/reports/<path:filename>')
def serve_report(filename):
    """提供报告文件访问"""
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/api/status')
def api_status():
    """API: 获取服务状态"""
    # 重复函数报告
    duplicate_files = list(OUTPUT_DIR.glob("duplicate_functions_report_*.html"))
    latest_duplicate = None
    if duplicate_files:
        latest = max(duplicate_files, key=lambda p: p.stat().st_mtime)
        latest_duplicate = {
            'name': latest.name,
            'mtime': datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
            'size': latest.stat().st_size
        }
    
    # 未注释函数报告
    uncommented_files = list(OUTPUT_DIR.glob("uncommented_functions_report*.html"))
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
def api_run_analysis(analysis_type):
    """API: 手动触发分析"""
    try:
        if analysis_type == 'duplicate':
            run_duplicate_analysis()
        elif analysis_type == 'uncommented':
            run_uncommented_analysis()
        elif analysis_type == 'all':
            run_all_analysis()
        else:
            return jsonify({'success': False, 'error': '无效的分析类型'}), 400
        
        return jsonify({'success': True, 'message': '分析完成'})
    except Exception as e:
        logger.error(f"API触发分析失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def init_scheduler():
    """初始化定时任务"""
    # 每天早上7:00运行完整分析
    scheduler.add_job(
        func=run_all_analysis,
        trigger=CronTrigger(hour=7, minute=0),
        id='daily_analysis',
        name='每日代码质量分析',
        replace_existing=True
    )
    
    logger.info("✅ 定时任务已配置: 每天 7:00 运行完整分析")
    scheduler.start()
    logger.info("✅ 调度器已启动")


if __name__ == '__main__':
    # 初始化定时任务
    init_scheduler()
    
    # 启动Flask应用
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 启动代码质量分析Web服务,监听端口 {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
