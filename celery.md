 Celery 异步任务方案

  基于当前项目架构，以下是使用 Celery 解决同步阻塞的详细方案。

  ---
  1. 依赖安装

  pip install celery redis

  requirements.txt 新增：
  celery>=5.3.0
  redis>=4.5.0

  ---
  2. 目录结构调整

  mericoComment/
  ├── src/
  │   ├── tasks/                    # [新增] Celery 任务模块
  │   │   ├── __init__.py
  │   │   ├── celery_app.py         # Celery 实例配置
  │   │   ├── analysis_tasks.py     # 分析类异步任务
  │   │   └── report_tasks.py       # 报告生成异步任务
  │   ├── api/
  │   │   └── routes/
  │   │       └── task_routes.py    # [新增] 任务状态查询 API

  ---
  3. Celery 配置

  src/tasks/celery_app.py
  from celery import Celery
  from src.config import get_config

  config = get_config()

  celery_app = Celery(
      'mericoComment',
      broker=config.REDIS_URL or 'redis://localhost:6379/0',
      backend=config.REDIS_URL or 'redis://localhost:6379/0',
      include=[
          'src.tasks.analysis_tasks',
          'src.tasks.report_tasks',
      ]
  )

  celery_app.conf.update(
      task_serializer='json',
      accept_content=['json'],
      result_serializer='json',
      timezone='Asia/Shanghai',
      enable_utc=True,
      task_track_started=True,
      result_expires=3600,  # 结果保留1小时
      task_soft_time_limit=300,  # 软超时5分钟
      task_time_limit=600,  # 硬超时10分钟
  )

  src/config/settings.py 新增配置项：
  @dataclass
  class Config:
      # ... 现有配置 ...
      REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

  ---
  4. 异步任务定义

  src/tasks/analysis_tasks.py
  from celery import shared_task
  from src.tasks.celery_app import celery_app
  from src.utils import LoggerFactory

  logger = LoggerFactory.get_logger(__name__)

  @celery_app.task(bind=True, max_retries=3)
  def analyze_uncommented_functions(self, repo_path: str, options: dict = None):
      """异步分析未注释函数"""
      try:
          self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '开始分析'})

          from src.core.agents import UncommentedFunctionsAgent

          with UncommentedFunctionsAgent() as agent:
              self.update_state(state='PROGRESS', meta={'progress': 30, 'status': '扫描代码'})
              result = agent.analyze(repo_path, **(options or {}))

          self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '完成'})
          return {'status': 'success', 'data': result}

      except Exception as e:
          logger.error(f"分析任务失败: {e}", exc_info=True)
          self.retry(exc=e, countdown=60)  # 60秒后重试


  @celery_app.task(bind=True)
  def analyze_duplicate_code(self, repo_path: str, options: dict = None):
      """异步分析重复代码"""
      try:
          self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '开始分析'})

          from src.core.fetchers import DuplicateFunctionsFetcher

          with DuplicateFunctionsFetcher() as fetcher:
              self.update_state(state='PROGRESS', meta={'progress': 50, 'status': '检测重复'})
              result = fetcher.fetch(repo_path, **(options or {}))

          return {'status': 'success', 'data': result}

      except Exception as e:
          logger.error(f"重复代码分析失败: {e}", exc_info=True)
          raise

  src/tasks/report_tasks.py
  from celery import shared_task
  from src.tasks.celery_app import celery_app
  from src.utils import LoggerFactory

  logger = LoggerFactory.get_logger(__name__)

  @celery_app.task(bind=True)
  def generate_weekly_report(self, entity_id: str, workspace_id: str):
      """异步生成周报"""
      try:
          self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '收集数据'})

          from src.core.generators import WeeklyReportGenerator

          generator = WeeklyReportGenerator()

          self.update_state(state='PROGRESS', meta={'progress': 30, 'status': '分析数据'})
          result = generator.generate(entity_id, workspace_id)

          self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '完成'})
          return {'status': 'success', 'data': result}

      except Exception as e:
          logger.error(f"周报生成失败: {e}", exc_info=True)
          raise

  ---
  5. API 层改造

  src/api/routes/task_routes.py
  from flask import Blueprint, jsonify, request
  from src.tasks.analysis_tasks import analyze_uncommented_functions, analyze_duplicate_code
  from src.tasks.report_tasks import generate_weekly_report
  from src.tasks.celery_app import celery_app

  task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

  @task_bp.post('/analyze/uncommented')
  def start_uncommented_analysis():
      """启动未注释函数分析任务"""
      data = request.get_json() or {}
      repo_path = data.get('repo_path')

      if not repo_path:
          return jsonify({'error': 'repo_path is required'}), 400

      task = analyze_uncommented_functions.delay(repo_path, data.get('options'))

      return jsonify({
          'task_id': task.id,
          'status': 'PENDING',
          'message': '任务已提交'
      }), 202


  @task_bp.post('/analyze/duplicate')
  def start_duplicate_analysis():
      """启动重复代码分析任务"""
      data = request.get_json() or {}
      repo_path = data.get('repo_path')

      if not repo_path:
          return jsonify({'error': 'repo_path is required'}), 400

      task = analyze_duplicate_code.delay(repo_path, data.get('options'))

      return jsonify({
          'task_id': task.id,
          'status': 'PENDING',
          'message': '任务已提交'
      }), 202


  @task_bp.post('/report/weekly')
  def start_weekly_report():
      """启动周报生成任务"""
      data = request.get_json() or {}
      entity_id = data.get('entity_id')
      workspace_id = data.get('workspace_id')

      if not entity_id or not workspace_id:
          return jsonify({'error': 'entity_id and workspace_id are required'}), 400

      task = generate_weekly_report.delay(entity_id, workspace_id)

      return jsonify({
          'task_id': task.id,
          'status': 'PENDING',
          'message': '任务已提交'
      }), 202


  @task_bp.get('/status/<task_id>')
  def get_task_status(task_id: str):
      """查询任务状态"""
      task = celery_app.AsyncResult(task_id)

      response = {
          'task_id': task_id,
          'status': task.state,
      }

      if task.state == 'PENDING':
          response['progress'] = 0
          response['message'] = '等待执行'
      elif task.state == 'PROGRESS':
          response['progress'] = task.info.get('progress', 0)
          response['message'] = task.info.get('status', '')
      elif task.state == 'SUCCESS':
          response['progress'] = 100
          response['result'] = task.result
      elif task.state == 'FAILURE':
          response['error'] = str(task.info)

      return jsonify(response)


  @task_bp.delete('/cancel/<task_id>')
  def cancel_task(task_id: str):
      """取消任务"""
      celery_app.control.revoke(task_id, terminate=True)
      return jsonify({'message': '任务已取消'})

  注册 Blueprint - src/api/app.py：
  from src.api.routes.task_routes import task_bp

  def create_app():
      app = Flask(__name__)
      # ... 现有代码 ...
      app.register_blueprint(task_bp)
      return app

  ---
  6. 前端轮询实现

  static/js/task-polling.js
  class TaskPoller {
      constructor(taskId, options = {}) {
          this.taskId = taskId;
          this.interval = options.interval || 2000;
          this.onProgress = options.onProgress || (() => {});
          this.onSuccess = options.onSuccess || (() => {});
          this.onError = options.onError || (() => {});
          this.timer = null;
      }

      start() {
          this.poll();
          this.timer = setInterval(() => this.poll(), this.interval);
      }

      stop() {
          if (this.timer) {
              clearInterval(this.timer);
              this.timer = null;
          }
      }

      async poll() {
          try {
              const response = await fetch(`/api/tasks/status/${this.taskId}`);
              const data = await response.json();

              if (data.status === 'PROGRESS') {
                  this.onProgress(data.progress, data.message);
              } else if (data.status === 'SUCCESS') {
                  this.stop();
                  this.onSuccess(data.result);
              } else if (data.status === 'FAILURE') {
                  this.stop();
                  this.onError(data.error);
              }
          } catch (error) {
              this.stop();
              this.onError(error.message);
          }
      }
  }

  // 使用示例
  async function startAnalysis(repoPath) {
      const response = await fetch('/api/tasks/analyze/uncommented', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_path: repoPath })
      });

      const { task_id } = await response.json();

      const poller = new TaskPoller(task_id, {
          onProgress: (progress, message) => {
              console.log(`进度: ${progress}% - ${message}`);
              updateProgressBar(progress, message);
          },
          onSuccess: (result) => {
              console.log('完成:', result);
              showResult(result);
          },
          onError: (error) => {
              console.error('失败:', error);
              showError(error);
          }
      });

      poller.start();
  }

  ---
  7. 启动命令

  启动 Redis
  redis-server

  启动 Celery Worker
  celery -A src.tasks.celery_app worker --loglevel=info

  启动 Flask 应用
  python run.py serve

  可选：启动 Celery Beat（定时任务）
  celery -A src.tasks.celery_app beat --loglevel=info

  ---
  8. Docker Compose 部署（可选）

  docker-compose.yml
  version: '3.8'

  services:
    redis:
      image: redis:7-alpine
      ports:
        - "6379:6379"
      volumes:
        - redis_data:/data

    web:
      build: .
      ports:
        - "8080:8080"
      environment:
        - REDIS_URL=redis://redis:6379/0
      depends_on:
        - redis

    celery_worker:
      build: .
      command: celery -A src.tasks.celery_app worker --loglevel=info
      environment:
        - REDIS_URL=redis://redis:6379/0
      depends_on:
        - redis

  volumes:
    redis_data:

  ---
  9. API 调用流程图

  ┌──────────┐     POST /api/tasks/analyze      ┌──────────┐
  │  Client  │ ─────────────────────────────────▶│  Flask   │
  └──────────┘                                   └────┬─────┘
       │                                              │
       │  返回 task_id (202 Accepted)                 │ .delay()
       │◀─────────────────────────────────────────────┤
       │                                              ▼
       │                                        ┌──────────┐
       │  GET /api/tasks/status/{task_id}       │  Redis   │
       │─────────────────────────────────────▶  │ (Broker) │
       │                                        └────┬─────┘
       │  返回 {status, progress}                    │
       │◀─────────────────────────────────────────────┤
       │                                              ▼
       │         (轮询直到 SUCCESS/FAILURE)     ┌──────────┐
       │                                        │  Celery  │
       │                                        │  Worker  │
       └────────────────────────────────────────└──────────┘

  ---
  总结

  | 组件          | 作用                             |
  |---------------|----------------------------------|
  | Redis         | 消息队列 + 结果存储              |
  | Celery Worker | 后台执行耗时任务                 |
  | Flask API     | 接收请求、返回 task_id、查询状态 |
  | 前端轮询      | 定时查询任务进度，展示结果       |

  这个方案可以让长时间的分析任务（代码分析、周报生成）在后台异步执行，API 立即返回，用户体验更好。

