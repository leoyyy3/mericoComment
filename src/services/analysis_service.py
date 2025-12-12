"""
代码分析服务

封装未注释函数分析和重复函数分析的业务逻辑
使用新架构的核心模块
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.utils import LoggerFactory
from src.core import UncommentedFunctionsAgent, DuplicateFunctionsFetcher, DataAnalyzer

logger = LoggerFactory.get_logger(__name__)


class AnalysisService:
    """
    代码分析服务

    提供未注释函数分析和重复函数分析的统一接口
    """

    def __init__(self, settings=None):
        """
        初始化分析服务

        Args:
            settings: 配置对象
        """
        self.settings = settings
        self._output_dir = Path(settings.output.output_dir if settings else 'output')
        self._output_dir.mkdir(exist_ok=True)

    def run_uncommented_analysis(self) -> Dict[str, Any]:
        """
        运行未注释函数分析

        Returns:
            分析结果
        """
        logger.info("开始执行未注释函数分析...")

        try:
            # 使用新架构的智能体
            with UncommentedFunctionsAgent(settings=self.settings) as agent:
                result = agent.run()

            # 获取生成的报告文件
            report_files = list(self._output_dir.glob('uncommented_functions_report*.html'))
            latest_report = max(report_files, key=lambda p: p.stat().st_mtime) if report_files else None

            logger.info("未注释函数分析完成")

            return {
                'status': 'success',
                'summary': result.get('summary', {}),
                'report_file': str(latest_report) if latest_report else None,
                'completed_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"未注释函数分析失败: {e}", exc_info=True)
            raise

    def run_duplicate_analysis(self) -> Dict[str, Any]:
        """
        运行重复函数分析

        Returns:
            分析结果
        """
        logger.info("开始执行重复函数分析...")

        try:
            # 使用新架构的获取器
            with DuplicateFunctionsFetcher(settings=self.settings) as fetcher:
                result = fetcher.run()

            # 获取最新报告
            html_files = sorted(self._output_dir.glob('duplicate_functions_report_*.html'))
            latest_report = str(html_files[-1]) if html_files else None

            logger.info("重复函数分析完成")

            return {
                'status': 'success',
                'total': result.get('total', 0),
                'successful': result.get('successful', 0),
                'failed': result.get('failed', 0),
                'report_file': latest_report,
                'completed_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"重复函数分析失败: {e}", exc_info=True)
            raise

    def run_all(self) -> Dict[str, Any]:
        """
        运行所有分析

        Returns:
            分析结果
        """
        logger.info("开始执行完整分析...")

        results = {
            'uncommented': None,
            'duplicate': None,
            'completed_at': None
        }

        # 运行未注释函数分析
        try:
            results['uncommented'] = self.run_uncommented_analysis()
        except Exception as e:
            results['uncommented'] = {
                'status': 'failed',
                'error': str(e)
            }

        # 运行重复函数分析
        try:
            results['duplicate'] = self.run_duplicate_analysis()
        except Exception as e:
            results['duplicate'] = {
                'status': 'failed',
                'error': str(e)
            }

        results['completed_at'] = datetime.now().isoformat()

        logger.info("完整分析完成")

        return results

    def analyze_data(self, data_file: str = None) -> DataAnalyzer:
        """
        分析已有数据

        Args:
            data_file: 数据文件路径，如果为 None 则使用最新文件

        Returns:
            DataAnalyzer 实例
        """
        analyzer = DataAnalyzer(classified_file=data_file, settings=self.settings)
        analyzer.run_full_analysis()
        return analyzer
