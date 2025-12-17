"""
智能体服务核心

管理对话状态、调用 LLM、执行工具
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from src.utils import LoggerFactory
from src.core import ZhipuAIClient
from .tools import ToolRegistry
from .prompts import PromptEngine

logger = LoggerFactory.get_logger(__name__)


class AgentService:
    def __init__(self, settings=None):
        self.settings = settings
        self.client = ZhipuAIClient(settings=settings)
        self.tools = ToolRegistry(settings=settings)
        self.prompt_engine = PromptEngine()
        
        # 简单的内存 Session 存储 (生产环境应使用 Redis)
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def clear_history(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id] = []

    def chat(self, session_id: str, message: str, token: str = None) -> Dict[str, Any]:
        
        # 预处理 token
        if token:
            token = token.strip()
        """
        处理用户消息
        
        Returns:
            {
                "response": "回复内容",
                "state": "IDLE" | "EXECUTING",
                "data": ... (可选的执行结果)
            }
        """
        if session_id not in self._sessions:
            logger.warning(f"Session {session_id} not found, recreating empty session.")
            self._sessions[session_id] = []

        history = self._sessions[session_id]
        history.append({"role": "user", "content": message})

        # 1. 构建 Prompt 并调用 LLM
        tools_schema = self.tools.get_all_tools_schema()
        messages = self.prompt_engine.build_messages(history, tools_schema)
        
        try:
            # First LLM Call (Think & Decide Tool)
            llm_response = self.client.invoke(
                messages=messages,
                tools=tools_schema
            )
            logger.info(f"LLM Response: {llm_response}")
            response_message = llm_response.choices[0].message
            logger.info(f"Response Message: {response_message}")
            history.append(response_message.model_dump())

            # 2. 检查是否有 Tool Calls
            if response_message.tool_calls:
                # Agent 决定调用工具
                tool_results = []
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # 注入 Token (如果前端传递了)
                    if token and "token" in self.tools.get_tool(function_name)["parameters"]["properties"]:
                         function_args["token"] = token
                    
                    # 执行工具
                    logger.info(f"Executing tool: {function_name} with args: {function_args}")
                    result = self.tools.execute(function_name, **function_args)
                    
                    # 将结果添加回对话历史
                    tool_result_msg = {
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call.id
                    }
                    history.append(tool_result_msg)
                    tool_results.append(result)

                # 3. Second LLM Call (Summarize Result)
                # 工具执行完后，再调一次 LLM 让其总结结果给用户
                final_response = self.client.invoke(
                    messages=self.prompt_engine.build_messages(history, tools_schema)
                    # 第二次调用通常不需要 tools，除非允许连续调用，这里简单处理
                )
                final_content = final_response.choices[0].message.content
                history.append({"role": "assistant", "content": final_content})
                
                return {
                    "response": final_content,
                    "state": "EXECUTED",
                    "data": tool_results
                }
            
            else:
                # 只是普通对话，没有调用工具
                return {
                    "response": response_message.content,
                    "state": "IDLE"
                }

        except Exception as e:
            logger.error(f"Agent chat error: {e}", exc_info=True)
            return {
                "response": "抱歉，我遇到了一些系统错误，请稍后再试。",
                "state": "ERROR"
            }
