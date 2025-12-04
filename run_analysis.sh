#!/bin/bash

# 设置错误时退出
set -e

# 日志文件
LOG_FILE="/app/log/analysis_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" | tee -a $LOG_FILE
echo "开始重复函数分析 - $(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

# 切换到应用目录
cd /app

# 运行分析脚本
echo "正在获取重复函数数据..." | tee -a $LOG_FILE
python fetch_duplicate_functions.py 2>&1 | tee -a $LOG_FILE

# 检查是否成功
if [ $? -eq 0 ]; then
    echo "✅ 分析完成!" | tee -a $LOG_FILE
    
    # 创建最新报告的符号链接
    LATEST_HTML=$(ls -t /app/output/duplicate_functions_report_*.html 2>/dev/null | head -1)
    if [ -n "$LATEST_HTML" ]; then
        ln -sf "$LATEST_HTML" /app/output/duplicate_functions_report_latest.html
        echo "✅ 已创建最新报告链接" | tee -a $LOG_FILE
    fi
else
    echo "❌ 分析失败!" | tee -a $LOG_FILE
    exit 1
fi

echo "========================================" | tee -a $LOG_FILE
echo "分析结束 - $(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
