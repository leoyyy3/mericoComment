"""
Chat API 路由

处理智能体对话请求
"""

from flask import Blueprint, request, jsonify, current_app
from src.agent.service import AgentService
from src.utils import ResponseFormatter, LoggerFactory

logger = LoggerFactory.get_logger(__name__)

chat_bp = Blueprint('chat', __name__)

# 全局 Agent Service 实例 (懒加载)
_agent_service = None

def get_agent_service():
    global _agent_service
    if _agent_service is None:
        settings = current_app.config.get('SETTINGS')
        _agent_service = AgentService(settings=settings)
    return _agent_service


@chat_bp.route('/session', methods=['POST'])
def create_session():
    """创建新会话"""
    try:
        service = get_agent_service()
        session_id = service.create_session()
        return ResponseFormatter.success({'session_id': session_id})
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return ResponseFormatter.internal_error(str(e))


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """发送消息"""
    try:
        data = request.get_json()
        if not data:
            return ResponseFormatter.bad_request("缺少请求体")

        session_id = data.get('session_id')
        message = data.get('message')
        token = data.get('token')
        logger.info(f"session_id: {session_id}, message: {message}, token: {token[:10] if token else 'None'}")
        
        if not session_id or not message:
            return ResponseFormatter.bad_request("缺少 session_id 或 message")

        service = get_agent_service()
        logger.info(f"Agent Service: {service}")
        result = service.chat(session_id, message, token=token)
        
        return ResponseFormatter.success(result)

    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return ResponseFormatter.internal_error(str(e))


@chat_bp.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """获取历史记录"""
    try:
        service = get_agent_service()
        history = service.get_history(session_id)
        # 过滤掉 tool 产生的中间消息，只返回 user 和 assistant 的 (可选，暂时全返回方便调试)
        return ResponseFormatter.success({'history': history})
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        return ResponseFormatter.internal_error(str(e))
