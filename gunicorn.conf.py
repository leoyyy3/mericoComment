'''
Author: leoyang liuyang2020@staff.hexun.com
Date: 2025-12-23 10:20:51
LastEditors: leoyang liuyang2020@staff.hexun.com
LastEditTime: 2025-12-23 15:50:54
Description: 
'''
"""
Gunicorn 配置文件

使用方法:
    gunicorn -c gunicorn.conf.py wsgi:app
"""
import os
import multiprocessing

# ============ 服务器绑定 ============
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8080')

# ============ Worker 配置 ============
# Worker 数量：一般 2-4 个足够
# 公式参考：CPU * 2 + 1（适用于 CPU 密集型，但对于 IO 密集型应用过多）
workers = int(os.getenv('GUNICORN_WORKERS', 4))

# Worker 类型
# - sync: 同步模式（默认）
# - gevent: 协程模式（适合 IO 密集型）
# - eventlet: 类似 gevent
# - gthread: 多线程模式
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# 每个 worker 的线程数（仅 gthread 模式有效）
threads = int(os.getenv('GUNICORN_THREADS', 2))

# 每个 worker 的最大连接数（仅 gevent/eventlet 有效）
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', 1000))

# ============ 超时配置 ============
# Worker 超时时间（秒）- 超时后 worker 会被杀死并重启
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))

# 优雅关闭超时
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Keep-alive 连接超时
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 5))

# ============ 进程管理 ============
# 最大请求数后重启 worker（防止内存泄漏）
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 10000))

# 随机抖动，防止所有 worker 同时重启
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 1000))

# 预加载应用（节省内存，但热重载不可用）
preload_app = os.getenv('GUNICORN_PRELOAD', 'false').lower() == 'true'

# ============ 日志配置 ============
# 访问日志：'-' 表示输出到 stdout
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')

# 错误日志：'-' 表示输出到 stderr
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')

# 日志级别：debug, info, warning, error, critical
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ============ 安全配置 ============
# 限制请求行大小（字节）
limit_request_line = 4094

# 限制请求头字段数量
limit_request_fields = 100

# 限制请求头字段大小（字节）
limit_request_field_size = 8190

# ============ 服务器钩子 ============
def on_starting(server):
    """服务器启动前 - 设置环境变量"""
    os.environ['GUNICORN_ARBITER_PID'] = str(server.pid)
    os.environ['SERVER_SOFTWARE'] = 'gunicorn'
    print(f"Gunicorn 正在启动，监听 {bind}")

def when_ready(server):
    """服务器准备就绪"""
    print(f"Gunicorn 已就绪，Workers: {workers}")

def worker_exit(server, worker):
    """Worker 退出时"""
    print(f"Worker {worker.pid} 已退出")

def post_fork(server, worker):
    """Worker 进程fork 后，标记为子进程"""
    os.environ['GUNICORN_WORKER_PID'] = str(worker.pid)

    # 子进程中不应该运行调度器
    os.environ['GUNICORN_IS_WORKER'] = 'true'

def on_exit(server):
    """服务器退出时"""
    print("Gunicorn 已关闭")
