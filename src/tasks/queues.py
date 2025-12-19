from enum import Enum
from rq import Queue
from .connection import redis_conn

class TaskQueue(str, Enum):
    DEFAULT = 'default'
    ANALYSIS = 'analysis'

_queues: dict[str, Queue] = {}

def get_queue(queue_type: TaskQueue = TaskQueue.DEFAULT) -> Queue:
    """获取队列实例"""
    if queue_type.value not in _queues:
        _queues[queue_type.value] = Queue(
            queue_type.value,
            connection=redis_conn
        )
    return _queues[queue_type.value]
