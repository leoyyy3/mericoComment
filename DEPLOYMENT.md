# Docker部署文档

## 概述

本项目提供Docker化部署方案,实现:
- ✅ 每天早上7:00自动运行重复函数分析
- ✅ 通过Web界面(端口8080)访问HTML报告
- ✅ 数据持久化存储
- ✅ 自动重启和健康检查

## 架构说明

```
Docker容器
├── Python应用 (分析脚本)
├── Cron (定时任务调度)
└── Nginx (Web服务器,端口8080)
```

## 快速开始

### 1. 构建并启动

```bash
# 使用docker-compose启动
docker-compose up -d

# 或者手动构建和运行
docker build -t duplicate-functions-analyzer .
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/log:/app/log \
  --name merico-duplicate-functions \
  duplicate-functions-analyzer
```

### 2. 访问报告

打开浏览器访问: `http://localhost:8080`

- 最新报告: `http://localhost:8080/duplicate_functions_report_latest.html`
- 所有报告列表: `http://localhost:8080/`

### 3. 查看日志

```bash
# 查看容器日志
docker-compose logs -f

# 查看分析日志
docker exec merico-duplicate-functions cat /var/log/cron/analysis.log

# 查看Nginx访问日志
docker exec merico-duplicate-functions tail -f /var/log/nginx/access.log
```

## 配置说明

### 定时任务

定时任务配置在Dockerfile中:
```
0 7 * * * /app/run_analysis.sh
```

如需修改执行时间,编辑Dockerfile中的cron表达式:
- `0 7 * * *` - 每天7:00
- `0 */6 * * *` - 每6小时
- `0 9,17 * * *` - 每天9:00和17:00

修改后需要重新构建镜像:
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 端口配置

默认端口为8080,如需修改,编辑`docker-compose.yml`:
```yaml
ports:
  - "9090:8080"  # 将宿主机9090端口映射到容器8080
```

### 数据持久化

数据通过Volume挂载持久化:
- `./output` - HTML报告和CSV文件
- `./log` - 分析日志

## 管理命令

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看状态
```bash
docker-compose ps
```

### 手动触发分析
```bash
docker exec merico-duplicate-functions /app/run_analysis.sh
```

### 进入容器
```bash
docker exec -it merico-duplicate-functions /bin/bash
```

### 查看cron任务
```bash
docker exec merico-duplicate-functions crontab -l
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker镜像定义 |
| `docker-compose.yml` | Docker编排配置 |
| `entrypoint.sh` | 容器启动脚本 |
| `run_analysis.sh` | 分析执行脚本 |
| `nginx.conf` | Nginx配置文件 |

## 故障排除

### 问题1: 容器无法启动

**检查日志:**
```bash
docker-compose logs
```

**常见原因:**
- 端口8080已被占用
- 配置文件缺失
- 权限问题

**解决方案:**
```bash
# 检查端口占用
lsof -i :8080

# 修改端口或停止占用端口的服务
```

### 问题2: 定时任务未执行

**检查cron日志:**
```bash
docker exec merico-duplicate-functions cat /var/log/cron/analysis.log
```

**手动测试:**
```bash
docker exec merico-duplicate-functions /app/run_analysis.sh
```

**验证cron配置:**
```bash
docker exec merico-duplicate-functions crontab -l
```

### 问题3: 无法访问Web界面

**检查Nginx状态:**
```bash
docker exec merico-duplicate-functions service nginx status
```

**检查端口映射:**
```bash
docker port merico-duplicate-functions
```

**重启Nginx:**
```bash
docker exec merico-duplicate-functions service nginx restart
```

### 问题4: 报告未生成

**检查Python脚本:**
```bash
docker exec merico-duplicate-functions python /app/fetch_duplicate_functions.py
```

**检查配置文件:**
```bash
docker exec merico-duplicate-functions cat /app/config.json
```

## 生产环境建议

### 1. 使用环境变量

创建`.env`文件:
```env
PORT=8080
TZ=Asia/Shanghai
```

修改`docker-compose.yml`:
```yaml
ports:
  - "${PORT}:8080"
environment:
  - TZ=${TZ}
```

### 2. 配置反向代理

使用Nginx或Traefik作为反向代理:
```nginx
server {
    listen 80;
    server_name duplicate-functions.example.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 配置HTTPS

使用Let's Encrypt证书:
```bash
certbot --nginx -d duplicate-functions.example.com
```

### 4. 监控和告警

添加健康检查和监控:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 5. 日志轮转

配置日志轮转避免磁盘占满:
```bash
# 在宿主机配置logrotate
/path/to/log/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 更新和维护

### 更新代码
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose down
docker-compose build
docker-compose up -d
```

### 清理旧报告
```bash
# 保留最近7天的报告
find ./output -name "duplicate_functions_*" -mtime +7 -delete
```

### 备份数据
```bash
# 备份output目录
tar -czf backup_$(date +%Y%m%d).tar.gz output/
```

## 安全建议

1. **限制访问**: 使用防火墙或反向代理限制访问
2. **定期更新**: 定期更新基础镜像和依赖
3. **最小权限**: 容器以非root用户运行
4. **网络隔离**: 使用Docker网络隔离
5. **敏感信息**: 使用Docker secrets管理敏感配置

## 性能优化

1. **资源限制**: 在docker-compose.yml中添加资源限制
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
```

2. **缓存优化**: 优化Dockerfile层缓存
3. **并发处理**: 如果项目较多,考虑并发分析

## 联系支持

如有问题,请查看:
- 项目文档: `README.md`
- 使用指南: `DISPLAY_GUIDE.md`
- 日志文件: `./log/`
