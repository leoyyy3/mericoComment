/**
 * 任务管理器 - 处理异步任务的提交和轮询
 */
class TaskManager {
    constructor(options = {}) {
        this.pollInterval = options.pollInterval || 2000;
        this.maxRetries = options.maxRetries || 100;
        this.activePollers = new Map();
    }

    /**
     * 提交分析任务
     */
    async submitAnalysis(type, repoPath, options = {}) {
        const endpoints = {
            'uncommented': '/api/tasks/analyze/uncommented',
            'duplicate': '/api/tasks/analyze/duplicate',
            'all': '/api/tasks/analyze/all'
        };

        const endpoint = endpoints[type];
        if (!endpoint) {
            throw new Error(`未知的分析类型: ${type}`);
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_path: repoPath, options })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '提交失败');
        }

        return response.json();
    }

    /**
     * 提交周报任务
     */
    async submitWeeklyReport(entityId, workspaceId) {
        const response = await fetch('/api/tasks/report/weekly', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entity_id: entityId, workspace_id: workspaceId })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '提交失败');
        }

        return response.json();
    }

    /**
     * 查询任务状态
     */
    async getStatus(taskId) {
        const response = await fetch(`/api/tasks/status/${taskId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '查询失败');
        }

        return response.json();
    }

    /**
     * 轮询任务直到完成
     */
    pollUntilDone(taskId, callbacks = {}) {
        const { onProgress, onSuccess, onError, onStatusChange } = callbacks;

        let retries = 0;

        const poll = async () => {
            try {
                const status = await this.getStatus(taskId);

                if (onStatusChange) {
                    onStatusChange(status);
                }

                switch (status.status) {
                    case 'finished':
                        this.stopPolling(taskId);
                        if (onSuccess) onSuccess(status.result);
                        break;

                    case 'failed':
                        this.stopPolling(taskId);
                        if (onError) onError(status.error);
                        break;

                    case 'started':
                        if (onProgress) onProgress(status.meta || {});
                        break;

                    case 'queued':
                        // 继续等待
                        break;
                }

                retries++;
                if (retries >= this.maxRetries) {
                    this.stopPolling(taskId);
                    if (onError) onError('轮询超时');
                }

            } catch (error) {
                this.stopPolling(taskId);
                if (onError) onError(error.message);
            }
        };

        // 立即执行一次，然后定时轮询
        poll();
        const timer = setInterval(poll, this.pollInterval);
        this.activePollers.set(taskId, timer);

        return taskId;
    }

    /**
     * 停止轮询
     */
    stopPolling(taskId) {
        const timer = this.activePollers.get(taskId);
        if (timer) {
            clearInterval(timer);
            this.activePollers.delete(taskId);
        }
    }

    /**
     * 取消任务
     */
    async cancelTask(taskId) {
        this.stopPolling(taskId);

        const response = await fetch(`/api/tasks/cancel/${taskId}`, {
            method: 'DELETE'
        });

        return response.json();
    }

    /**
     * 获取队列统计
     */
    async getQueueStats() {
        const response = await fetch('/api/tasks/queue/stats');
        return response.json();
    }
}

// 导出全局实例
window.taskManager = new TaskManager();