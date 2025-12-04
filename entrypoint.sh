#!/bin/bash

echo "启动重复函数分析服务..."

# 启动Nginx
echo "启动Nginx..."
service nginx start

# 启动Cron
echo "启动Cron服务..."
cron

# 首次运行分析(可选,如果想在容器启动时立即生成一次报告)
echo "执行首次分析..."
/app/run_analysis.sh

# 保持容器运行,并输出cron日志
echo "服务已启动,监听端口8080"
echo "Cron任务将在每天早上7:00运行"
tail -f /var/log/cron.log /var/log/nginx/access.log /var/log/nginx/error.log
