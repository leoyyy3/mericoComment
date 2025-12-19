#!/usr/bin/env python
"""
RQ Worker 启动脚本

使用方法:
    python worker.py                    # 启动默认队列 worker
    python worker.py --queues high default low  # 指定队列优先级
    python worker.py --burst            # burst 模式（处理完退出）
"""
import argparse
import sys
import os
import platform
from pathlib import Path

# 修复 macOS 上的 Fork 安全错误 (objc_initializeAfterForkError)
# 必须在进程启动的最早期设置，如果当前未设置，则设置后重启进程
if platform.system() == 'Darwin':
    if os.environ.get('OBJC_DISABLE_INITIALIZE_FORK_SAFETY') != 'YES':
        print("macOS detected: Restarting worker with OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES")
        os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"Failed to restart process: {e}")

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rq import Worker, Queue
from src.tasks.connection import redis_conn
from src.utils import LoggerFactory

logger = LoggerFactory.get_logger('rq.worker')


def main():
    parser = argparse.ArgumentParser(description='RQ Worker')
    parser.add_argument(
        '--queues', '-q',
        nargs='+',
        default=['high', 'default', 'low'],
        help='要监听的队列（按优先级排序）'
    )
    parser.add_argument(
        '--burst', '-b',
        action='store_true',
        help='Burst 模式：处理完所有任务后退出'
    )
    parser.add_argument(
        '--name', '-n',
        default=None,
        help='Worker 名称'
    )

    args = parser.parse_args()
    print("DEBUG: Args parsed")

    try:
        print("DEBUG: Initializing queues...")
        queues = [Queue(name, connection=redis_conn) for name in args.queues]
        print("DEBUG: Queues initialized")

        print("DEBUG: Initializing worker...")
        worker = Worker(
            queues,
            name=args.name,
            connection=redis_conn
        )
        print("DEBUG: Worker initialized")

        logger.info(f"Worker 启动，监听队列: {args.queues}")

        worker.work(
            burst=args.burst,
            with_scheduler=True  # 启用调度器支持
        )
    except Exception as e:
        print(f"ERROR: 发生错误: {e}")
        logger.error(f"Worker 运行出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()