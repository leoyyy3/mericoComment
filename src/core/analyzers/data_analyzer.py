"""
未注释函数数据分析器

提供深入的统计分析和可视化报告
使用新架构的公共模块
"""

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from jinja2 import Environment, FileSystemLoader

from src.utils import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class Config:
    """配置常量"""
    TOP_N_ITEMS = 20
    TOP_PROJECTS_BEST = 10
    TOP_TYPES_DISPLAY = 15
    TOP_CROSS_DIMENSION = 5
    BAR_CHART_WIDTH = 40
    SECTION_WIDTH = 80
    SUBSECTION_WIDTH = 78
    TOP_RANKING_THRESHOLD = 3
    MEDIUM_RANKING_THRESHOLD = 10
    SUCCESS_RATE_HIGH = 90
    SUCCESS_RATE_MEDIUM = 70
    MAX_ERRORS_DISPLAY = 10
    DEFAULT_CSV_FILENAME = "uncommented_functions_export.csv"
    DEFAULT_HTML_FILENAME = "uncommented_functions_report.html"
    CSV_ENCODING = "utf-8-sig"
    JSON_ENCODING = "utf-8"


@dataclass
class ColorScheme:
    """终端颜色方案"""
    HEADER: str = '\033[95m'
    BLUE: str = '\033[94m'
    CYAN: str = '\033[96m'
    GREEN: str = '\033[92m'
    YELLOW: str = '\033[93m'
    RED: str = '\033[91m'
    BOLD: str = '\033[1m'
    UNDERLINE: str = '\033[4m'
    END: str = '\033[0m'

    @classmethod
    def no_color(cls) -> 'ColorScheme':
        """返回无颜色方案"""
        return cls(
            HEADER='', BLUE='', CYAN='', GREEN='',
            YELLOW='', RED='', BOLD='', UNDERLINE='', END=''
        )


colors = ColorScheme()


class DataAnalyzer:
    """未注释函数数据分析器"""

    def __init__(self, classified_file: str = None, data: dict = None, settings=None):
        """
        初始化分析器

        Args:
            classified_file: 归类数据文件路径（可选）
            data: 直接传入的数据字典（可选）
            settings: Settings 配置对象（可选）
        """
        self.classified_file = classified_file
        self.settings = settings
        self._project_function_count_cache = None
        self.repo_id_to_name = self._load_repo_mapping()

        if data is not None:
            self.data = data
        elif classified_file is not None:
            self.data = self.load_data()
        else:
            self.data = self.load_latest_data()

    def _load_repo_mapping(self) -> Dict[str, str]:
        """加载 repo_id 到 repo_name 的映射"""
        try:
            # 尝试多个可能的路径
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / 'assets' / 'repoId_repoName_list.json',
                Path('assets/repoId_repoName_list.json'),
                Path('./assets/repoId_repoName_list.json')
            ]

            for mapping_file in possible_paths:
                if mapping_file.exists():
                    with open(mapping_file, 'r', encoding=Config.JSON_ENCODING) as f:
                        mapping_list = json.load(f)
                    return {item['repoId']: item['repoName'] for item in mapping_list}

            logger.warning("未找到 repo 映射文件")
            return {}
        except Exception as e:
            logger.warning(f"加载 repo 映射文件失败: {e}")
            return {}

    def get_repo_name(self, repo_id: str) -> str:
        """根据 repo_id 获取 repo_name"""
        return self.repo_id_to_name.get(repo_id, repo_id)

    @property
    def project_function_count(self) -> Counter:
        """缓存项目函数统计数据"""
        if self._project_function_count_cache is None:
            self._project_function_count_cache = Counter()
            all_uncommented_functions = self.data.get("all_uncommented_functions", [])
            for func in all_uncommented_functions:
                if repo_id := func.get("repo_id"):
                    self._project_function_count_cache[repo_id] += 1
        return self._project_function_count_cache

    def load_data(self) -> Dict[str, Any]:
        """从文件加载数据"""
        try:
            with open(self.classified_file, 'r', encoding=Config.JSON_ENCODING) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"文件不存在: {self.classified_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON格式无效: {e}")
            raise
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            raise

    def load_latest_data(self) -> Dict[str, Any]:
        """加载最新的归类数据文件"""
        try:
            files = list(Path('./output').glob('classified_results_*.json'))
            if not files:
                logger.error("未找到归类数据文件")
                raise FileNotFoundError("未找到归类数据文件")

            latest_file = max(files, key=lambda p: p.stat().st_mtime)
            self.classified_file = str(latest_file)
            logger.info(f"使用最新的数据文件: {self.classified_file}")

            with open(self.classified_file, 'r', encoding=Config.JSON_ENCODING) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载最新数据失败: {e}")
            raise

    @staticmethod
    def print_section_header(title: str) -> None:
        """打印章节标题"""
        print(f"\n{colors.BOLD}{colors.CYAN}{'=' * Config.SECTION_WIDTH}{colors.END}")
        print(f"{colors.BOLD}{colors.HEADER}{title.center(Config.SECTION_WIDTH)}{colors.END}")
        print(f"{colors.BOLD}{colors.CYAN}{'=' * Config.SECTION_WIDTH}{colors.END}\n")

    @staticmethod
    def print_subsection(title: str) -> None:
        """打印小节标题"""
        print(f"\n{colors.BOLD}{colors.BLUE}▶ {title}{colors.END}")
        print(f"{colors.CYAN}{'─' * Config.SUBSECTION_WIDTH}{colors.END}")

    @staticmethod
    def print_bar_chart(label: str, value: int, total: int, width: int = None, color: str = None) -> None:
        """打印条形图"""
        if width is None:
            width = Config.BAR_CHART_WIDTH
        if color is None:
            color = colors.GREEN
        percentage = (value / total * 100) if total > 0 else 0
        filled = int(percentage / 100 * width)
        bar = '█' * filled + '░' * (width - filled)
        print(f"{label:30s} │ {color}{bar}{colors.END} │ {colors.BOLD}{value:6d}{colors.END} ({percentage:5.1f}%)")

    @staticmethod
    def get_severity_color(severity: str) -> str:
        """根据严重程度返回颜色"""
        severity_colors = {
            'critical': colors.RED,
            'high': colors.RED,
            'medium': colors.YELLOW,
            'low': colors.GREEN,
            'info': colors.CYAN,
        }
        return severity_colors.get(severity.lower(), colors.END)

    def analyze_severity_distribution(self) -> None:
        """分析严重程度分布"""
        self.print_section_header("复杂度分布分析")
        by_severity = self.data.get("by_severity", {})
        total = sum(by_severity.values())

        if total == 0:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        sorted_severity = sorted(by_severity.items(), key=lambda x: x[1], reverse=True)
        for severity, count in sorted_severity:
            color = self.get_severity_color(severity)
            self.print_bar_chart(severity, count, total, color=color)

        print(f"\n{colors.BOLD}总计: {total:,} 个未注释函数{colors.END}")

    def analyze_type_distribution(self) -> None:
        """分析类型分布"""
        self.print_section_header(f"函数类型分布分析 (Top {Config.TOP_N_ITEMS})")
        by_type = self.data.get("by_type", {})
        total = sum(by_type.values())

        if total == 0:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:Config.TOP_N_ITEMS]
        for i, (issue_type, count) in enumerate(sorted_types, 1):
            rank_color = colors.YELLOW if i <= Config.TOP_RANKING_THRESHOLD else colors.END
            label = f"{rank_color}{i:2d}.{colors.END} {issue_type}"
            self.print_bar_chart(label, count, total, color=colors.BLUE)

        print(f"\n{colors.BOLD}统计信息:{colors.END}")
        print(f"  • 总类型数: {colors.CYAN}{len(by_type)}{colors.END}")
        print(f"  • 未注释函数数: {colors.CYAN}{total:,}{colors.END}")

    def analyze_rule_distribution(self) -> None:
        """分析规则/作者分布"""
        self.print_section_header(f"作者分布分析 (Top {Config.TOP_N_ITEMS})")
        by_rule = self.data.get("by_rule", {})
        total = sum(by_rule.values())

        if total == 0:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        sorted_rules = sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:Config.TOP_N_ITEMS]
        for i, (rule, count) in enumerate(sorted_rules, 1):
            rank_color = colors.YELLOW if i <= Config.TOP_RANKING_THRESHOLD else colors.END
            label = f"{rank_color}{i:2d}.{colors.END} {rule[:35]}"
            self.print_bar_chart(label, count, total, color=colors.CYAN)

        print(f"\n{colors.BOLD}统计信息:{colors.END}")
        print(f"  • 作者总数: {colors.CYAN}{len(by_rule)}{colors.END}")
        print(f"  • 未注释函数总数: {colors.CYAN}{total:,}{colors.END}")

    def analyze_project_quality(self) -> None:
        """分析各项目未注释函数情况"""
        self.print_section_header("项目未注释函数排名")
        project_function_count = self.project_function_count

        if len(project_function_count) == 0:
            print(f"{colors.YELLOW}⚠ 无有效项目数据{colors.END}")
            return

        sorted_projects = project_function_count.most_common(20)

        self.print_subsection("未注释函数最多的项目 (Top 20)")
        print(f"\n{'排名':<6} {'项目名称':<45} {'未注释函数数':>12}")
        print(f"{colors.CYAN}{'─' * 78}{colors.END}")

        for i, (repo_id, count) in enumerate(sorted_projects, 1):
            repo_name = self.get_repo_name(repo_id)
            if i <= 3:
                rank_icon = f"{colors.RED}🔥{colors.END}"
            elif i <= 10:
                rank_icon = f"{colors.YELLOW}⚠️{colors.END}"
            else:
                rank_icon = "  "
            print(f"{rank_icon} {i:2d}.  {repo_name:<45} {colors.RED}{count:>8,}{colors.END} 个")

        # 未注释函数最少的项目
        self.print_subsection("未注释函数最少的项目 (Top 10)")
        print(f"\n{'排名':<6} {'项目名称':<45} {'未注释函数数':>12}")
        print(f"{colors.CYAN}{'─' * 78}{colors.END}")

        least_functions = sorted(project_function_count.items(), key=lambda x: x[1])[:10]
        for i, (repo_id, count) in enumerate(least_functions, 1):
            repo_name = self.get_repo_name(repo_id)
            icon = f"{colors.GREEN}✓{colors.END}"
            print(f"{icon} {i:2d}.  {repo_name:<45} {colors.GREEN}{count:>8,}{colors.END} 个")

        # 统计汇总
        avg_functions = sum(project_function_count.values()) / len(project_function_count)
        print(f"\n{colors.BOLD}统计汇总:{colors.END}")
        print(f"  • 项目总数: {colors.CYAN}{len(project_function_count)}{colors.END}")
        print(f"  • 平均未注释函数数: {colors.CYAN}{avg_functions:.1f}{colors.END}")

    def analyze_cross_dimension(self) -> None:
        """交叉维度分析"""
        self.print_section_header("交叉维度分析")
        all_uncommented_functions = self.data.get("all_uncommented_functions", [])

        if not all_uncommented_functions:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        severity_type = defaultdict(lambda: defaultdict(int))
        for func in all_uncommented_functions:
            severity = func.get("severity", "unknown")
            func_type = func.get("type", "unknown")
            severity_type[severity][func_type] += 1

        self.print_subsection("各复杂度级别下的 Top 5 函数类型")
        for severity in sorted(severity_type.keys()):
            color = self.get_severity_color(severity)
            print(f"\n{color}{colors.BOLD}{severity.upper()}{colors.END}")
            types = severity_type[severity]
            sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (func_type, count) in enumerate(sorted_types, 1):
                print(f"  {i}. {func_type}: {colors.BOLD}{count}{colors.END}")

    def generate_summary_report(self) -> None:
        """生成总结报告"""
        summary = self.data.get("summary", {})

        width = 80
        print(f"\n{colors.BOLD}{colors.HEADER}{'=' * width}{colors.END}")
        title = "📊 Merico 项目未注释函数分析总结报告"
        print(f"{colors.BOLD}{colors.HEADER}{title.center(width + 2)}{colors.END}")
        print(f"{colors.BOLD}{colors.HEADER}{'=' * width}{colors.END}\n")

        print(f"{colors.CYAN}⏰ 分析时间:{colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.print_subsection("基本统计")
        total_projects = summary.get('total_projects', 0)
        successful_projects = summary.get('successful_projects', 0)
        failed_projects = summary.get('failed_projects', 0)
        total_uncommented_functions = summary.get('total_uncommented_functions', 0)

        print(f"\n  📁 总项目数: {colors.BOLD}{colors.CYAN}{total_projects}{colors.END}")
        print(f"  ✓ 成功项目数: {colors.BOLD}{colors.GREEN}{successful_projects}{colors.END}")
        print(f"  ✗ 失败项目数: {colors.BOLD}{colors.RED}{failed_projects}{colors.END}")
        print(f"  📝 总未注释函数数: {colors.BOLD}{colors.YELLOW}{total_uncommented_functions:,}{colors.END}")

        if successful_projects > 0:
            avg_functions = total_uncommented_functions / successful_projects
            print(f"  📈 平均每项目未注释函数数: {colors.BOLD}{colors.CYAN}{avg_functions:.1f}{colors.END}")

        if total_projects > 0:
            success_rate = (successful_projects / total_projects) * 100
            if success_rate >= 90:
                rate_color = colors.GREEN
                rate_icon = "✓"
            elif success_rate >= 70:
                rate_color = colors.YELLOW
                rate_icon = "⚠"
            else:
                rate_color = colors.RED
                rate_icon = "✗"
            print(f"\n  {rate_icon} 数据获取成功率: {rate_color}{colors.BOLD}{success_rate:.1f}%{colors.END}")

        errors = self.data.get("errors", [])
        if errors:
            self.print_subsection(f"失败的项目 ({len(errors)})")
            print()
            for i, error in enumerate(errors[:10], 1):
                print(f"  {colors.RED}✗{colors.END} {i:2d}. {error.get('repo_id', 'Unknown')[:50]}")
                print(f"       {colors.YELLOW}原因: {error.get('error', 'Unknown error')}{colors.END}")
            if len(errors) > 10:
                print(f"\n  {colors.CYAN}... 还有 {len(errors) - 10} 个失败项目{colors.END}")

    def export_csv(self, output_file: str = None) -> None:
        """导出为 CSV 格式"""
        import csv

        if output_file is None:
            output_file = f"./output/{Config.DEFAULT_CSV_FILENAME}"

        all_uncommented_functions = self.data.get("all_uncommented_functions", [])

        if not all_uncommented_functions:
            logger.warning("无数据可导出")
            return

        fieldnames = set()
        for func in all_uncommented_functions:
            fieldnames.update(func.keys())
        fieldnames = sorted(fieldnames)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', newline='', encoding=Config.CSV_ENCODING) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_uncommented_functions)

        logger.info(f"CSV 导出完成: {output_file}")
        print(f"\n{colors.GREEN}✓ 未注释函数数据已导出{colors.END}")
        print(f"  文件路径: {colors.CYAN}{output_file}{colors.END}")
        print(f"  总记录数: {colors.BOLD}{len(all_uncommented_functions):,}{colors.END}")

    def export_html(self, output_file: str = None) -> None:
        """生成 HTML 可视化报告"""
        if output_file is None:
            output_file = f"./output/{Config.DEFAULT_HTML_FILENAME}"

        try:
            summary = self.data.get("summary", {})
            by_severity = self.data.get("by_severity", {})
            by_type = self.data.get("by_type", {})
            project_function_count = self.project_function_count

            # 准备图表数据
            severity_labels = list(by_severity.keys())
            severity_data = list(by_severity.values())
            severity_color_map = {
                'critical': '#dc2626', 'high': '#ef4444',
                'medium': '#f59e0b', 'low': '#10b981', 'info': '#3b82f6'
            }
            severity_colors = [severity_color_map.get(s.lower(), '#6b7280') for s in severity_labels]

            type_items = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:Config.TOP_TYPES_DISPLAY]
            type_labels = [item[0] for item in type_items]
            type_data = [item[1] for item in type_items]

            project_rankings = [
                (i, (self.get_repo_name(repo_id), count))
                for i, (repo_id, count) in enumerate(project_function_count.most_common(20), 1)
            ]

            # 查找模板目录
            possible_template_dirs = [
                Path(__file__).parent.parent.parent.parent / 'templates',
                Path('templates'),
                Path('./templates')
            ]

            template_dir = None
            for td in possible_template_dirs:
                if td.exists() and (td / 'report.html').exists():
                    template_dir = td
                    break

            if template_dir is None:
                logger.error("未找到模板目录")
                return

            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('report.html')

            html_content = template.render(
                generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                summary=summary,
                severity_labels=severity_labels,
                severity_data=severity_data,
                severity_colors=severity_colors,
                type_labels=type_labels,
                type_data=type_data,
                project_rankings=project_rankings
            )

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML 报告生成完成: {output_file}")
            print(f"\n{colors.GREEN}✓ HTML 报告已生成{colors.END}")
            print(f"  文件路径: {colors.CYAN}{output_file}{colors.END}")

        except Exception as e:
            logger.error(f"生成 HTML 报告失败: {e}")

    def run_full_analysis(self) -> None:
        """运行完整分析"""
        self.generate_summary_report()
        self.analyze_severity_distribution()
        self.analyze_type_distribution()
        self.analyze_rule_distribution()
        self.analyze_project_quality()
        self.analyze_cross_dimension()
