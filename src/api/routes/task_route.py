"""
异步任务 API 路由
"""
from flask import Blueprint, jsonify, request
from rq.job import Job
from rq.exceptions import NoSuchJobError

from src.tasks import (
    get_redis_connection,
    get_queue,
    TaskQueue,
    analyze_uncommented,
    analyze_duplicate,
    analyze_all,
    # generate_weekly_report,
)

task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

redis_conn = get_redis_connection()


# ============ 任务提交 ============

@task_bp.post('/analyze/uncommented')
def submit_uncommented_analysis():
    """提交未注释函数分析任务"""
    data = request.get_json() or {}
    repo_path = data.get('repo_path')

    if not repo_path:
        return jsonify({'error': 'repo_path 是必填参数'}), 400

    queue = get_queue(TaskQueue.DEFAULT)
    job = queue.enqueue(
        analyze_uncommented,
        repo_path,
        data.get('options'),
        job_timeout=600,      # 10 分钟超时
        result_ttl=3600,      # 结果保留 1 小时
        failure_ttl=86400,    # 失败记录保留 1 天
    )

    return jsonify({
        'task_id': job.id,
        'status': 'queued',
        'message': '任务已提交，请轮询状态接口获取结果'
    }), 202


@task_bp.post('/analyze/duplicate')
def submit_duplicate_analysis():
    """提交重复代码分析任务"""
    data = request.get_json() or {}
    repo_path = data.get('repo_path')

    if not repo_path:
        return jsonify({'error': 'repo_path 是必填参数'}), 400

    queue = get_queue(TaskQueue.DEFAULT)
    job = queue.enqueue(
        analyze_duplicate,
        repo_path,
        data.get('options'),
        job_timeout=600,
        result_ttl=3600,
    )

    return jsonify({
        'task_id': job.id,
        'status': 'queued',
        'message': '任务已提交'
    }), 202


@task_bp.post('/analyze/all')
def submit_all_analysis():
    """提交全量分析任务"""
    data = request.get_json() or {}
    repo_path = data.get('repo_path')

    if not repo_path:
        return jsonify({'error': 'repo_path 是必填参数'}), 400

    # 全量分析使用低优先级队列，避免阻塞其他任务
    queue = get_queue(TaskQueue.LOW)
    job = queue.enqueue(
        analyze_all,
        repo_path,
        data.get('options'),
        job_timeout=1200,  # 20 分钟
        result_ttl=3600,
    )

    return jsonify({
        'task_id': job.id,
        'status': 'queued',
        'message': '全量分析任务已提交'
    }), 202


@task_bp.post('/report/weekly')
def submit_weekly_report():
    """提交周报生成任务"""
    data = request.get_json() or {}
    entity_id = data.get('entity_id')
    workspace_id = data.get('workspace_id')

    if not entity_id or not workspace_id:
        return jsonify({'error': 'entity_id 和 workspace_id 是必填参数'}), 400

    queue = get_queue(TaskQueue.DEFAULT)
    job = queue.enqueue(
        # generate_weekly_report,
        entity_id,
        workspace_id,
        job_timeout=600,
        result_ttl=3600,
    )

    return jsonify({
        'task_id': job.id,
        'status': 'queued',
        'message': '周报生成任务已提交'
    }), 202


# ============ 任务状态查询 ============

@task_bp.get('/status/<task_id>')
def get_task_status(task_id: str):
    """查询任务状态"""
    try:
        job = Job.fetch(task_id, connection=redis_conn)
    except NoSuchJobError:
        return jsonify({'error': '任务不存在或已过期'}), 404

    response = {
        'task_id': task_id,
        'status': job.get_status(),
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'ended_at': job.ended_at.isoformat() if job.ended_at else None,
    }

    status = job.get_status()

    if status == 'finished':
        response['result'] = job.result
    elif status == 'failed':
        response['error'] = str(job.exc_info) if job.exc_info else '未知错误'
    elif status == 'started':
        # 可选：从 job.meta 获取进度信息
        response['meta'] = job.meta

    return jsonify(response)


@task_bp.get('/result/<task_id>')
def get_task_result(task_id: str):
    """获取任务结果（仅成功的任务）"""
    try:
        job = Job.fetch(task_id, connection=redis_conn)
    except NoSuchJobError:
        return jsonify({'error': '任务不存在或已过期'}), 404

    if job.get_status() != 'finished':
        return jsonify({
            'error': '任务尚未完成',
            'status': job.get_status()
        }), 400

    return jsonify(job.result)


# ============ 任务管理 ============

@task_bp.delete('/cancel/<task_id>')
def cancel_task(task_id: str):
    """取消任务"""
    try:
        job = Job.fetch(task_id, connection=redis_conn)
    except NoSuchJobError:
        return jsonify({'error': '任务不存在'}), 404

    status = job.get_status()

    if status in ('finished', 'failed'):
        return jsonify({'error': f'任务已结束，状态: {status}'}), 400

    job.cancel()

    return jsonify({
        'message': '任务已取消',
        'task_id': task_id
    })


@task_bp.get('/queue/stats')
def get_queue_stats():
    """获取队列统计信息"""
    stats = {}

    for queue_type in TaskQueue:
        queue = get_queue(queue_type)
        stats[queue_type.value] = {
            'queued': len(queue),
            'started': queue.started_job_registry.count,
            'finished': queue.finished_job_registry.count,
            'failed': queue.failed_job_registry.count,
        }

    return jsonify(stats)