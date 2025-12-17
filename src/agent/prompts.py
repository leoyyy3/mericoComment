"""
提示词引擎

管理 System Prompt 和对话上下文构建
"""

from typing import List, Dict, Any
import json

class PromptEngine:
    def __init__(self):
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        return """你是一个智能代码质量分析助手，负责帮助用户运行代码分析任务和生成周报。

你的核心能力：
1. 分析代码质量：可以运行重复代码检测或未注释函数检测。
2. 生成周报：根据 TAPD 数据生成项目周报。

交互原则：
- 如果用户指令模糊（如“生成周报”但未提供项目ID），你必须追问缺失的参数。
- 在执行耗时操作前，请先告知用户你即将开始执行。
- 回复要简洁、专业、友好。
- 关于 API Token：除非用户在对话中明确提供了新的 Token（通常是长字符串），否则在调用工具时请不要传递 token 参数（或传 null），系统会自动使用配置文件中的默认 Token。不要编造 Token。

已知项目ID映射（供参考，如果是这些项目可以直接推断 ID）：
- hexun_wcms -> entity_id: ..., workspace_id: ... (需要用户提供或从配置读取)
- 暂时如果用户没提供 ID，请直接询问 Entity ID 和 Workspace ID。

当前时间：{current_time}
"""

    def build_messages(self, history: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建发送给 LLM 的消息列表"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        return messages
