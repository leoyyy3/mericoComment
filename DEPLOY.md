# Docker 部署指南

本文档说明如何在另一台服务器上使用 Docker 部署 Merico 代码质量分析平台。

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 开放端口：8080（Web）、6379（Redis，可选）

## 快速部署步骤

### 1. 安装 Docker（如未安装）

#### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Linux (CentOS/RHEL)

```bash
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

#### Windows

1. **下载 Docker Desktop**
   - 访问 https://www.docker.com/products/docker-desktop/
   - 下载 Windows 版本安装包

2. **安装要求**
   - Windows 10/11 64位（专业版、企业版或教育版）
   - 启用 WSL 2（Windows Subsystem for Linux）
   - 启用 Hyper-V 虚拟化

3. **启用 WSL 2**
   ```powershell
   # 以管理员身份运行 PowerShell
   wsl --install
   wsl --set-default-version 2
   ```

4. **安装并启动 Docker Desktop**
   - 运行安装程序，按提示完成安装
   - 重启电脑
   - 启动 Docker Desktop
   - 等待 Docker 引擎启动（托盘图标变绿）

5. **验证安装**
   ```powershell
   docker --version
   docker-compose --version
   ```

#### macOS

```bash
# 使用 Homebrew 安装
brew install --cask docker

# 或下载 Docker Desktop
# https://www.docker.com/products/docker-desktop/
```

### 2. 准备项目文件

```bash
# 方式一：从 Git 克隆
git clone <repository-url> mericoComment
cd mericoComment

# 方式二：直接复制项目文件到服务器
scp -r ./mericoComment user@server:/path/to/
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

**必须配置的变量**：
```bash
# .env 文件内容
ZHIPU_API_KEY=your-zhipu-api-key
MERICO_TOKEN=your-merico-token
MERICO_API_URL=https://your-merico-api/buffet/re/quality/listFunctions
MERICO_DUPLICATE_URL=https://your-merico-api/buffet/api/tech_debt/duplicated_group
```

### 4. 配置 config.json（可选）

如果需要使用 TAPD 功能，需要配置 `config.json`：

```bash
cp config.json.template config.json
nano config.json
```

### 5. 启动服务

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 6. 验证部署

```bash
# 检查健康状态
curl http://localhost:8080/api/health

# 预期返回
{"success": true, "data": {"status": "healthy"}}
```

---

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f [app|worker|redis]

# 重新构建镜像
docker-compose up -d --build

# 进入容器调试
docker-compose exec app bash

# 启动包含 RQ Dashboard 的监控
docker-compose --profile monitoring up -d
```

---

## 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| app | 8080 | Web API 服务 |
| worker | - | RQ 异步任务处理 |
| redis | 6379 | 任务队列存储 |
| rq-dashboard | 9181 | 任务监控面板（可选） |

---

## 数据持久化

以下目录会持久化到宿主机：

```
./output/       → 分析报告输出
./log/          → 应用日志
redis_data      → Redis 数据（Docker Volume）
```

---

## 生产环境优化

### 1. 使用 Nginx 反向代理

```nginx
# /etc/nginx/sites-available/merico
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 配置 HTTPS（使用 Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.example.com
```

### 3. 设置防火墙

```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. 配置日志轮转

```bash
# /etc/logrotate.d/merico
/path/to/mericoComment/log/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
}
```

---

## 故障排查

### 服务无法启动

```bash
# 检查日志
docker-compose logs app

# 常见问题：
# 1. 端口被占用：修改 docker-compose.yml 中的端口映射
# 2. 环境变量未配置：检查 .env 文件
# 3. 配置文件错误：检查 config.json 格式
```

### Redis 连接失败

```bash
# 检查 Redis 服务
docker-compose logs redis

# 测试连接
docker-compose exec redis redis-cli ping
```

### 内存不足

```bash
# 检查内存使用
docker stats

# 减少 Worker 数量
# 修改 docker-compose.yml 中的 GUNICORN_WORKERS=2
```

---

## 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

---

## 备份与恢复

### 备份

```bash
# 备份输出文件
tar -czf backup_$(date +%Y%m%d).tar.gz output/

# 备份 Redis 数据
docker-compose exec redis redis-cli BGSAVE
docker cp merico-redis:/data/dump.rdb ./backup/
```

### 恢复

```bash
# 恢复输出文件
tar -xzf backup_20241223.tar.gz

# 恢复 Redis 数据
docker cp ./backup/dump.rdb merico-redis:/data/
docker-compose restart redis
```
