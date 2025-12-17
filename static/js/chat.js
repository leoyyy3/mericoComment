document.addEventListener('DOMContentLoaded', () => {
    const chatWidget = document.getElementById('chatWidget');
    const toggleBtn = document.getElementById('chatToggleBtn');
    const closeBtn = document.getElementById('chatCloseBtn');
    const messagesContainer = document.getElementById('chatMessages');
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');

    let sessionId = localStorage.getItem('chat_session_id');

    // 初始化会话
    async function initSession() {
        if (!sessionId) {
            try {
                const response = await fetch('/api/chat/session', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    sessionId = data.data.session_id;
                    localStorage.setItem('chat_session_id', sessionId);
                }
            } catch (error) {
                console.error('Failed to init session:', error);
            }
        }
    }

    // Toggle Chat
    toggleBtn.addEventListener('click', () => {
        chatWidget.classList.add('open');
        toggleBtn.style.transform = 'scale(0)';
        initSession();
    });

    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        chatWidget.classList.remove('open');
        toggleBtn.style.transform = 'scale(1)';
    });

    // Send Message
    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, 'user');
        input.value = '';

        // Show typing
        const typingId = showTyping();

        // 获取 Token (兼容 index.html 定义的 key)
        const token = localStorage.getItem('merico_api_token');

        try {
            const body = {
                session_id: sessionId,
                message: text
            };

            if (token) {
                body.token = token;
            }

            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();

            removeTyping(typingId);

            if (data.success) {
                const result = data.data;
                addMessage(result.response, 'assistant');

                // Handle data/actions if needed
                if (result.data) {
                    console.log('Task executed:', result.data);
                    // 可以添加一些UI反馈，比如 "生成成功，点击查看"
                }
            } else {
                addMessage('出错啦：' + data.error.message, 'assistant');
            }
        } catch (error) {
            removeTyping(typingId);
            addMessage('网络错误，请稍后再试', 'assistant');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    function addMessage(text, role) {
        const div = document.createElement('div');
        div.className = `message ${role}`;

        // 简单的 Markdown 处理 (可以引入 marked.js)
        div.innerHTML = text.replace(/\n/g, '<br>');

        // 解析链接
        div.innerHTML = div.innerHTML.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" style="color: inherit; text-decoration: underline;">$1</a>'
        );

        messagesContainer.appendChild(div);
        scrollToBottom();
    }

    function showTyping() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'typing-indicator';
        div.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        messagesContainer.appendChild(div);
        scrollToBottom();
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
