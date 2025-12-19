// 页面交互示例
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analysis-form');
    const progressBar = document.getElementById('progress-bar');
    const resultContainer = document.getElementById('result');
    const statusText = document.getElementById('status-text');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const repoPath = document.getElementById('repo-path').value;
        const analysisType = document.getElementById('analysis-type').value;

        // 显示进度条
        progressBar.style.display = 'block';
        progressBar.value = 0;
        statusText.textContent = '提交任务中...';
        resultContainer.innerHTML = '';

        try {
            // 提交任务
            const { task_id } = await taskManager.submitAnalysis(analysisType, repoPath);

            statusText.textContent = `任务已提交 (ID: ${task_id})，等待执行...`;

            // 轮询直到完成
            taskManager.pollUntilDone(task_id, {
                onStatusChange: (status) => {
                    const statusMap = {
                        'queued': '排队中...',
                        'started': '分析中...',
                        'finished': '完成',
                        'failed': '失败'
                    };
                    statusText.textContent = statusMap[status.status] || status.status;

                    if (status.status === 'started') {
                        progressBar.removeAttribute('value'); // 显示动画
                    }
                },

                onSuccess: (result) => {
                    progressBar.value = 100;
                    statusText.textContent = '分析完成！';
                    resultContainer.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                },

                onError: (error) => {
                    progressBar.value = 0;
                    statusText.textContent = `错误: ${error}`;
                    resultContainer.innerHTML = `<div class="error">${error}</div>`;
                }
            });

        } catch (error) {
            statusText.textContent = `提交失败: ${error.message}`;
        }
    });
});