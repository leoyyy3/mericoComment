# 使用 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖、cron和nginx
RUN apt-get update && apt-get install -y \
    cron \
    nginx \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 设置时区为中国时间
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY config.json .
COPY repoIds_simple.json .
COPY assets/ ./assets/
COPY fetch_duplicate_functions.py .
COPY display_duplicate_functions.py .

# 创建输出目录
RUN mkdir -p /app/output /app/log /var/log/cron

# 复制执行脚本
COPY run_analysis.sh /app/run_analysis.sh
RUN chmod +x /app/run_analysis.sh

# 配置cron任务 (每天早上7:00运行)
RUN echo "0 7 * * * /app/run_analysis.sh >> /var/log/cron/analysis.log 2>&1" > /etc/cron.d/analysis-cron
RUN chmod 0644 /etc/cron.d/analysis-cron
RUN crontab /etc/cron.d/analysis-cron

# 创建cron日志文件
RUN touch /var/log/cron.log

# 复制Nginx配置
COPY nginx.conf /etc/nginx/sites-available/default

# 复制启动脚本
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 暴露端口
EXPOSE 8080

# 设置启动命令
CMD ["entrypoint.sh"]
