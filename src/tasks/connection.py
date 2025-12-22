from redis import Redis
import logging
import sys
from pathlib import Path
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
# 加载 .env 文件中的环境变量
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

port = os.getenv('REDIS_PORT', '6379')
redis_host = os.getenv('REDIS_HOST', '192.168.20.17')

def get_redis_connection():
    """
    获取 Redis 连接，带超时和错误处理
    """
    try:
        conn = Redis(
            host=redis_host,
            port=port,
            db=0,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=False
        )
        # 尝试 ping 以验证连接
        conn.ping()
        return conn
    except Exception as e:
        print(f"CRITICAL: 无法连接到 Redis (192.168.20.17): {e}")
        raise

