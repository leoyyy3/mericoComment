"""
周报生成服务

封装周报生成的业务逻辑
使用新架构的公共模块
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class WeeklyReportService:
    """
    周报生成服务

    封装周报生成的业务逻辑，提供统一接口
    """

    def __init__(self, settings=None):
        """
        初始化周报服务

        Args:
            settings: 配置对象
        """
        self.settings = settings
        self._output_dir = Path(
            settings.output.output_dir if settings else 'output'
        ) / 'weekly_reports'
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._generator = None
        self._init_generator()

    def _init_generator(self):
        """初始化周报生成器"""
        try:
            # 使用新架构的周报生成器
            from src.core.generators import WeeklyReportGenerator

            if self.settings:
                # 优先使用 Settings 对象
                self._generator = WeeklyReportGenerator(settings=self.settings)
            else:
                # 回退到配置文件
                self._generator = WeeklyReportGenerator(config_path='config.json')

            logger.info("周报生成器初始化成功")

        except ImportError as e:
            logger.warning(f"周报生成器模块未找到: {e}")
            self._generator = None
        except Exception as e:
            logger.error(f"周报生成器初始化失败: {e}")
            self._generator = None

    def generate(
        self,
        entity_id: str,
        workspace_id: str,
        custom_prompt: Optional[str] = None,
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        生成周报

        Args:
            entity_id: 实体 ID
            workspace_id: 工作空间 ID
            custom_prompt: 自定义提示词
            save_to_file: 是否保存到文件

        Returns:
            生成结果
        """
        if not self._generator:
            raise RuntimeError("周报生成器未初始化")

        logger.info(f"开始生成周报: entity_id={entity_id}")

        # 确定输出文件路径
        output_file = None
        if save_to_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"weekly_report_{entity_id}_{timestamp}.md"
            output_file = str(self._output_dir / filename)

        # 生成周报
        report = self._generator.generate_report(
            entity_id=entity_id,
            workspace_id=workspace_id,
            output_file=output_file,
            custom_prompt=custom_prompt
        )

        result = {
            'report': report,
            'generated_at': datetime.now().isoformat()
        }

        if output_file:
            result['file_path'] = output_file

        logger.info("周报生成完成")

        return result

    def get_commits(
        self,
        entity_id: str,
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取提交记录

        Args:
            entity_id: 实体 ID
            workspace_id: 工作空间 ID

        Returns:
            提交记录列表
        """
        if not self._generator:
            raise RuntimeError("周报生成器未初始化")

        logger.info(f"获取提交记录: entity_id={entity_id}")

        commits = self._generator.tapd_client.fetch_all_commits(entity_id, workspace_id)
        commits_info = self._generator.tapd_client.extract_commit_info(commits)

        return commits_info

    def find_reports(
        self,
        entity_id: str,
        latest_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        查找指定项目的周报

        Args:
            entity_id: 实体 ID
            latest_only: 是否只返回最新的

        Returns:
            周报列表
        """
        pattern = f"weekly_report_{entity_id}_*.md"
        files = sorted(self._output_dir.glob(pattern), reverse=True)

        if not files:
            return []

        if latest_only:
            files = files[:1]

        reports = []
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()

                stat = file.stat()
                reports.append({
                    'file_name': file.name,
                    'file_path': str(file),
                    'content': content,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"读取文件失败 {file}: {e}")

        return reports
