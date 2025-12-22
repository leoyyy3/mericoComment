🔴 P0 - 必须立即处理（安全关键）

1. 移除硬编码的敏感信息

问题：config.json 中包含真实的 API Key 和 Token

// 当前存在的问题
"token": "123",
"zhipu_ai": { "api_key": "8e000ceae949460384284a803d67d752.xxx" },
"tapd": { "cookies": { "tapdsession": "xxx", "t_u": "xxx" } }

改进：
- 使用环境变量替代所有敏感配置
- 创建 .env 文件（已在 .gitignore 中）
- 从 Git 历史中清除已泄露的凭证

2. 修复 Redis 连接硬编码

位置：src/tasks/connection.py:9-15

# 当前：硬编码内网 IP
conn = Redis(host='192.168.20.17', port=6379, ...)

# 应改为：
conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    ...
)

3. 实现 API 认证机制

问题：所有 API 端点无认证保护，任何人可调用

建议：添加 Token 认证中间件

from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not validate_token(token):
            return ResponseFormatter.error('Unauthorized', status_code=401)
        return f(*args, **kwargs)
    return decorated

4. 修复路径遍历漏洞

位置：src/api/routes/analysis.py:203-213

# 当前：存在目录遍历风险
return send_from_directory(output_dir, filename)

# 应添加路径验证
file_path = (output_dir / filename).resolve()
if not str(file_path).startswith(str(output_dir.resolve())):
    return ResponseFormatter.error('Invalid path', status_code=403)

5. 使用生产级 WSGI 服务器

问题：run.py 使用 Flask 开发服务器

# 当前
app.run(host=args.host, port=args.port, debug=args.debug)

改进：创建 wsgi.py 并使用 Gunicorn

# wsgi.py
from src.api import create_app
app = create_app()

# 启动命令
gunicorn -w 4 -b 0.0.0.0:8080 -k gevent wsgi:app

---
🟠 P1 - 短期实施（1-2 周）

6. 添加 CORS 配置

# src/api/app.py
from flask_cors import CORS

CORS(app,
    origins=os.getenv('CORS_ORIGINS', 'https://your-domain.com').split(','),
    allow_headers=['Content-Type', 'Authorization'])

7. 配置 HTTPS/TLS

使用 Nginx 反向代理：

server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/static/;
        expires 30d;
    }
}

8. 完善健康检查

位置：src/api/routes/health.py

@health_bp.route('/health', methods=['GET'])
def health_check():
    checks = {'app': 'ok'}

    # 检查 Redis
    try:
        redis_conn.ping()
        checks['redis'] = 'ok'
    except:
        checks['redis'] = 'error'

    status = 'healthy' if all(v == 'ok' for v in checks.values()) else 'degraded'
    return ResponseFormatter.success({'status': status, 'checks': checks})

9. 会话存储迁移到 Redis

问题：src/agent/service.py 使用内存存储会话

# 当前：应用重启丢失所有会话
self._sessions: Dict[str, List[Dict]] = {}

# 应改为 Redis 存储
def create_session(self):
    session_id = str(uuid.uuid4())
    self.redis.setex(f'session:{session_id}', 86400, json.dumps([]))
    return session_id

10. 配置日志轮转

# src/utils/logger.py
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    log_file,
    maxBytes=100*1024*1024,  # 100MB
    backupCount=10
)

11. 创建 Docker 支持

Dockerfile：
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8080/api/health || exit 1
EXPOSE 8080
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "wsgi:app"]

docker-compose.yml：
version: '3.8'
services:
redis:
    image: redis:7-alpine
    volumes:
    - redis_data:/data

app:
    build: .
    ports:
    - "8080:8080"
    environment:
    - ENV=production
    - REDIS_HOST=redis
    - ZHIPU_API_KEY=${ZHIPU_API_KEY}
    - MERICO_TOKEN=${MERICO_TOKEN}
    depends_on:
    - redis
    volumes:
    - ./output:/app/output

worker:
    build: .
    command: python worker.py
    environment:
    - REDIS_HOST=redis
    depends_on:
    - redis

volumes:
redis_data:

---
🟡 P2 - 中期完善（2-4 周）

| 项目          | 说明                                  |
|---------------|---------------------------------------|
| Rate Limiting | 防止 API 滥用，使用 Flask-Limiter     |
| 请求重试优化  | 使用指数退避策略替代固定延迟          |
| 数据备份策略  | 定时备份 output/ 到 S3/OSS            |
| 监控告警      | 集成 Prometheus + Grafana             |
| CI/CD 流程    | GitHub Actions / GitLab CI 自动部署   |
| 依赖版本锁定  | 使用 pip-tools 生成 requirements.lock |

---
📋 部署检查清单

安全：
[ ] 移除所有硬编码凭证，使用环境变量
[ ] 实现 API 认证机制
[ ] 配置 HTTPS/TLS
[ ] 添加 CORS 白名单
[ ] 修复路径遍历漏洞
[ ] 禁用 DEBUG 模式

性能：
[ ] 使用 Gunicorn 替代 Flask 开发服务器
[ ] 配置 Nginx 反向代理
[ ] 启用静态文件缓存和 gzip 压缩

可靠性：
[ ] 会话存储迁移到 Redis
[ ] 配置日志轮转
[ ] 实现详细健康检查
[ ] 配置数据备份

运维：
[ ] 创建 Dockerfile 和 docker-compose.yml
[ ] 编写部署文档
[ ] 配置监控告警

---
⏱ 预估工作量

| 优先级 | 内容                      | 工作量 |
|--------|---------------------------|--------|
| P0     | 安全修复 + WSGI 服务器    | 3-5 天 |
| P1     | HTTPS + Docker + 日志优化 | 5-7 天 |
| P2     | 监控 + CI/CD + 备份       | 5-7 天 |
