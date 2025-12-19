from redis import Redis
import logging

def get_redis_connection():
    """
    获取 Redis 连接，带超时和错误处理
    """
    try:
        conn = Redis(
            host='192.168.20.17',
            port=6379,
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

# 为了兼容旧代码，保留这个变量，但可能在导入时就报错
try:
    redis_conn = Redis(host='192.168.20.17', port=6379, db=0, socket_timeout=5, socket_connect_timeout=5)
except:
    redis_conn = None