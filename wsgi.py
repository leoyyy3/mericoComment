#!/usr/bin/env python3
"""
WSGI 入口点 - 用于生产环境部署

使用方法:
    # 使用 Gunicorn 启动
    gunicorn wsgi:app

    # 指定配置文件启动
    gunicorn -c gunicorn.conf.py wsgi:app

    # 快速启动（4 workers）
    gunicorn -w 4 -b 0.0.0.0:8080 wsgi:app
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.api import create_app

# 创建应用实例 - Gunicorn 会导入并使用这个变量
app = create_app()

if __name__ == '__main__':
    # 仅用于本地调试，生产环境使用 Gunicorn
    app.run(host='0.0.0.0', port=8080, debug=True)
