"""
智能体工具注册表

负责将底层服务封装为 Agent 可调用的工具
"""

from typing import Dict, Any, Callable, List
from src.services import AnalysisService, WeeklyReportService
from src.utils import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class ToolRegistry:
    """工具注册表"""

    def __init__(self, settings=None):
        self.settings = settings
        self.analysis_service = AnalysisService(settings=settings)
        self.weekly_service = WeeklyReportService(settings=settings)
        self._tools = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        self.register(
            name="run_analysis",
            description="运行代码质量分析（重复函数或未注释函数）",
            func=self._tool_run_analysis,
            parameters={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["all", "uncommented", "duplicate"],
                        "description": "分析类型：all(全部), uncommented(未注释), duplicate(重复)"
                    },
                    "token": {
                        "type": "string",
                        "description": "Merico API Token (可选，如果用户提供了 Token 则填入)"
                    }
                },
                "required": ["type"]
            }
        )

        self.register(
            name="generate_weekly_report",
            description="生成项目周报",
            func=self._tool_generate_weekly_report,
            parameters={
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "TAPD 实体 ID (项目标识)"},
                    "workspace_id": {"type": "string", "description": "TAPD 工作空间 ID"},
                    "custom_prompt": {"type": "string", "description": "自定义提示词（可选）"}
                },
                "required": ["entity_id", "workspace_id"]
            }
        )
        
        self.register(
            name="get_project_status",
            description="查询项目分析状态或历史报告",
            func=self._tool_get_project_status,
            parameters={
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "项目实体 ID"}
                },
                "required": ["entity_id"]
            }
        )

    def register(self, name: str, description: str, func: Callable, parameters: Dict[str, Any]):
        """注册新工具"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "func": func,
            "parameters": parameters
        }

    def get_tool(self, name: str) -> Dict[str, Any]:
        """获取工具定义"""
        return self._tools.get(name)

    def get_all_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的 Schema（供 LLM 使用）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具 {name} 不存在")
        
        logger.info(f"Agent 调用工具: {name}, 参数: {kwargs}")
        try:
            return tool["func"](**kwargs)
        except Exception as e:
            logger.error(f"工具执行失败: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    # === Tool Implementations ===

    def _tool_run_analysis(self, type: str = "all", token: str = None) -> Dict[str, Any]:
        if type == "all":
            return self.analysis_service.run_all(token=token)
        elif type == "uncommented":
            return self.analysis_service.run_uncommented_analysis(token=token)
        elif type == "duplicate":
            return self.analysis_service.run_duplicate_analysis(token=token)
        else:
            return {"status": "error", "message": f"未知的分析类型: {type}"}

    def _tool_generate_weekly_report(self, entity_id: str, workspace_id: str, custom_prompt: str = None) -> Dict[str, Any]:
        return self.weekly_service.generate(
            entity_id=entity_id,
            workspace_id=workspace_id,
            custom_prompt=custom_prompt
        )

    def _tool_get_project_status(self, entity_id: str) -> Dict[str, Any]:
        # 获取该项目的最近周报
        reports = self.weekly_service.find_reports(entity_id, latest_only=True)
        if reports:
            return {"status": "found", "latest_report": reports[0]}
        else:
            return {"status": "not_found", "message": "未找到相关报告"}
