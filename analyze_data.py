"""
未注释函数分析器 - 分析项目中未添加文档注释的函数
提供深入的统计分析和可视化报告
"""

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from jinja2 import Environment, FileSystemLoader


class Config:
    """配置常量"""
    # 显示配置
    TOP_N_ITEMS = 20  # Top N 项目数
    TOP_PROJECTS_BEST = 10  # 显示表现最好的项目数
    TOP_TYPES_DISPLAY = 15  # HTML报告中显示的类型数
    TOP_CROSS_DIMENSION = 5  # 交叉维度分析显示的类型数

    # 图表配置
    BAR_CHART_WIDTH = 40  # 条形图宽度
    SECTION_WIDTH = 80  # 章节宽度
    SUBSECTION_WIDTH = 78  # 小节宽度

    # 排名阈值
    TOP_RANKING_THRESHOLD = 3  # 顶级排名阈值（前3名）
    MEDIUM_RANKING_THRESHOLD = 10  # 中等排名阈值（前10名）

    # 成功率阈值
    SUCCESS_RATE_HIGH = 90  # 高成功率阈值
    SUCCESS_RATE_MEDIUM = 70  # 中等成功率阈值

    # 错误显示配置
    MAX_ERRORS_DISPLAY = 10  # 最多显示的错误数

    # 文件名配置
    DEFAULT_CSV_FILENAME = "uncommented_functions_export.csv"
    DEFAULT_HTML_FILENAME = "uncommented_functions_report.html"

    # 编码配置
    CSV_ENCODING = "utf-8-sig"
    JSON_ENCODING = "utf-8"


@dataclass
class ColorScheme:
    """终端颜色方案"""
    header: str = '\033[95m'
    blue: str = '\033[94m'
    cyan: str = '\033[96m'
    GREEN: str = '\033[92m'
    yellow: str = '\033[93m'
    RED: str = '\033[91m'
    bold: str = '\033[1m'
    underline: str = '\033[4m'
    END: str = '\033[0m'

    @classmethod
    def no_color(cls) -> 'ColorScheme':
        """返回无颜色方案"""
        return cls(
            header='',
            blue='',
            cyan='',
            green='',
            yellow='',
            red='',
            bold='',
            underline='',
            end=''
        )


# 全局颜色方案实例
colors = ColorScheme()


class DataAnalyzer:
    """未注释函数数据分析器"""

    def __init__(self, classified_file: str = None, data: dict = None):
        """
        初始化分析器

        Args:
            classified_file: 归类数据文件路径（可选）
            data: 直接传入的数据字典（可选）

        Note:
            classified_file 和 data 至少提供一个
        """
        self.classified_file = classified_file
        self._project_function_count_cache = None

        if data is not None:
            # 如果直接提供了数据，使用该数据
            self.data = data
        elif classified_file is not None:
            # 如果提供了文件路径，从文件加载
            self.data = self.load_data()
        else:
            # 两者都没提供，尝试查找最新文件
            self.data = self.load_latest_data()

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
            print(f"{colors.RED}错误: 文件不存在 {self.classified_file}{colors.END}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"{colors.RED}错误: JSON格式无效 - {e}{colors.END}")
            sys.exit(1)
        except PermissionError:
            print(f"{colors.RED}错误: 没有读取权限 {self.classified_file}{colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"{colors.RED}错误: 加载数据失败 - {e}{colors.END}")
            sys.exit(1)

    def load_latest_data(self) -> Dict[str, Any]:
        """加载最新的归类数据文件"""
        try:
            files = list(Path('./output').glob('raw_results_*.json'))
            if not files:
                print(f"{colors.RED}错误: 未找到归类数据文件{colors.END}")
                print("请先运行数据采集或提供数据文件")
                sys.exit(1)

            # 使用最新的文件
            latest_file = max(files, key=lambda p: p.stat().st_mtime)
            self.classified_file = str(latest_file)
            print(f"{colors.CYAN}使用最新的数据文件: {colors.BOLD}{self.classified_file}{colors.END}\n")

            with open(self.classified_file, 'r', encoding=Config.JSON_ENCODING) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{colors.RED}错误: 文件不存在{colors.END}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"{colors.RED}错误: JSON格式无效 - {e}{colors.END}")
            sys.exit(1)
        except PermissionError:
            print(f"{colors.RED}错误: 没有读取权限{colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"{colors.RED}错误: 加载最新数据失败 - {e}{colors.END}")
            sys.exit(1)

    @staticmethod
    def print_section_header(title: str) -> None:
        """打印美化的章节标题"""
        print(f"\n{colors.BOLD}{colors.CYAN}{'=' * Config.SECTION_WIDTH}{colors.END}")
        print(f"{colors.BOLD}{colors.HEADER}{title.center(Config.SECTION_WIDTH)}{colors.END}")
        print(f"{colors.BOLD}{colors.CYAN}{'=' * Config.SECTION_WIDTH}{colors.END}\n")

    @staticmethod
    def print_subsection(title: str) -> None:
        """打印美化的小节标题"""
        print(f"\n{colors.BOLD}{colors.BLUE}▶ {title}{colors.END}")
        print(f"{colors.CYAN}{'─' * Config.SUBSECTION_WIDTH}{colors.END}")

    @staticmethod
    def print_bar_chart(
        label: str,
        value: int,
        total: int,
        width: int = None,
        color: str = None
    ) -> None:
        """打印美化的条形图"""
        if width is None:
            width = Config.BAR_CHART_WIDTH
        if color is None:
            color = colors.green
        percentage = (value / total * 100) if total > 0 else 0
        filled = int(percentage / 100 * width)
        bar = '█' * filled + '░' * (width - filled)

        print(f"{label:30s} │ {color}{bar}{colors.end} │ {colors.bold}{value:6d}{colors.end} ({percentage:5.1f}%)")

    @staticmethod
    def get_severity_color(severity: str) -> str:
        """根据严重程度返回颜色"""
        severity_colors = {
            'critical': colors.red,
            'high': colors.red,
            'medium': colors.yellow,
            'low': colors.green,
            'info': colors.cyan,
        }
        return severity_colors.get(severity.lower(), colors.end)

    def analyze_severity_distribution(self) -> None:
        """分析严重程度分布"""
        self.print_section_header("复杂度分布分析")

        by_severity = self.data.get("by_severity", {})
        total = sum(by_severity.values())

        if total == 0:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        # 排序并计算百分比
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

        # 排序并显示 Top N
        sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:Config.TOP_N_ITEMS]

        for i, (issue_type, count) in enumerate(sorted_types, 1):
            rank_color = colors.YELLOW if i <= Config.TOP_RANKING_THRESHOLD else colors.END
            label = f"{rank_color}{i:2d}.{colors.END} {issue_type}"
            self.print_bar_chart(label, count, total, color=colors.BLUE)

        print(f"\n{colors.BOLD}统计信息:{colors.END}")
        print(f"  • 总类型数: {colors.CYAN}{len(by_type)}{colors.END}")
        print(f"  • 未注释函数数: {colors.CYAN}{total:,}{colors.END}")

    def analyze_rule_distribution(self) -> None:
        """分析规则分布"""
        self.print_section_header(f"作者分布分析 (Top {Config.TOP_N_ITEMS})")

        by_rule = self.data.get("by_rule", {})
        total = sum(by_rule.values())

        if total == 0:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        # 排序并显示 Top N
        sorted_rules = sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:Config.TOP_N_ITEMS]

        for i, (rule, count) in enumerate(sorted_rules, 1):
            rank_color = colors.YELLOW if i <= Config.TOP_RANKING_THRESHOLD else colors.END
            label = f"{rank_color}{i:2d}.{colors.END} {rule[:35]}"
            self.print_bar_chart(label, count, total, color=colors.CYAN)

        print(f"\n{colors.BOLD}统计信息:{colors.END}")
        print(f"  • 作者总数: {colors.CYAN}{len(by_rule)}{colors.END}")
        print(f"  • 未注释函数总数: {colors.CYAN}{total:,}{colors.END}")

    def analyze_project_quality(self):
        """分析各项目未注释函数情况"""
        self.print_section_header("项目未注释函数排名")

        # 使用缓存的项目函数统计数据
        project_function_count = self.project_function_count

        if len(project_function_count) == 0:
            print(f"{colors.YELLOW}⚠ 无有效项目数据{colors.END}")
            return

        # 排序并显示 Top 20
        sorted_projects = project_function_count.most_common(20)

        self.print_subsection("未注释函数最多的项目 (Top 20)")
        print(f"\n{'排名':<6} {'项目ID':<45} {'未注释函数数':>12}")
        print(f"{colors.CYAN}{'─' * 78}{colors.END}")

        for i, (repo_id, count) in enumerate(sorted_projects, 1):
            if i <= 3:
                rank_icon = f"{colors.RED}🔥{colors.END}"
            elif i <= 10:
                rank_icon = f"{colors.YELLOW}⚠️{colors.END}"
            else:
                rank_icon = "  "

            print(f"{rank_icon} {i:2d}.  {repo_id:<45} {colors.RED}{count:>8,}{colors.END} 个")

        # 未注释函数最少的项目
        self.print_subsection("未注释函数最少的项目 (Top 10)")
        print(f"\n{'排名':<6} {'项目ID':<45} {'未注释函数数':>12}")
        print(f"{colors.CYAN}{'─' * 78}{colors.END}")

        least_functions = sorted(project_function_count.items(), key=lambda x: x[1])[:10]
        for i, (repo_id, count) in enumerate(least_functions, 1):
            icon = f"{colors.GREEN}✓{colors.END}"
            print(f"{icon} {i:2d}.  {repo_id:<45} {colors.GREEN}{count:>8,}{colors.END} 个")

        # 统计汇总
        avg_functions = sum(project_function_count.values()) / len(project_function_count)
        print(f"\n{colors.BOLD}统计汇总:{colors.END}")
        print(f"  • 项目总数: {colors.CYAN}{len(project_function_count)}{colors.END}")
        print(f"  • 平均未注释函数数: {colors.CYAN}{avg_functions:.1f}{colors.END}")
        print(f"  • 最大未注释函数数: {colors.RED}{sorted_projects[0][1]:,}{colors.END} ({sorted_projects[0][0][:30]}...)")
        print(f"  • 最小未注释函数数: {colors.GREEN}{least_functions[0][1]:,}{colors.END} ({least_functions[0][0][:30]}...)")

    def analyze_cross_dimension(self):
        """交叉维度分析"""
        self.print_section_header("交叉维度分析")

        all_uncommented_functions = self.data.get("all_uncommented_functions", [])

        if not all_uncommented_functions:
            print(f"{colors.YELLOW}⚠ 无数据{colors.END}")
            return

        # 复杂度 x 类型
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

    def generate_summary_report(self):
        """生成总结报告"""
        summary = self.data.get("summary", {})

        # 打印标题
        width = 80
        print(f"\n{colors.BOLD}{colors.HEADER}{'=' * width}{colors.END}")
        title = "📊 Merico 项目未注释函数分析总结报告"
        print(f"{colors.BOLD}{colors.HEADER}{title.center(width + 2)}{colors.END}")
        print(f"{colors.BOLD}{colors.HEADER}{'=' * width}{colors.END}\n")

        # 时间信息
        print(f"{colors.CYAN}⏰ 分析时间:{colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 基本统计
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

        # 数据质量评估
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

        # 失败项目列表
        errors = self.data.get("errors", [])
        if errors:
            self.print_subsection(f"失败的项目 ({len(errors)})")
            print()
            for i, error in enumerate(errors[:10], 1):
                print(f"  {colors.RED}✗{colors.END} {i:2d}. {error.get('repo_id', 'Unknown')[:50]}")
                print(f"       {colors.YELLOW}原因: {error.get('error', 'Unknown error')}{colors.END}")
            if len(errors) > 10:
                print(f"\n  {colors.CYAN}... 还有 {len(errors) - 10} 个失败项目{colors.END}")

    def export_csv(self, output_file: str = "uncommented_functions_export.csv"):
        """导出为 CSV 格式"""
        try:
            import csv

            all_uncommented_functions = self.data.get("all_uncommented_functions", [])

            if not all_uncommented_functions:
                print(f"\n{colors.YELLOW}⚠ 无数据可导出{colors.END}")
                return

            # 获取所有字段
            fieldnames = set()
            for func in all_uncommented_functions:
                fieldnames.update(func.keys())

            fieldnames = sorted(fieldnames)

            # 写入 CSV
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_uncommented_functions)

            print(f"\n{colors.GREEN}✓ 未注释函数数据已导出{colors.END}")
            print(f"  文件路径: {colors.CYAN}{output_file}{colors.END}")
            print(f"  总记录数: {colors.BOLD}{len(all_uncommented_functions):,}{colors.END}")

        except Exception as e:
            print(f"\n{colors.RED}✗ 导出 CSV 失败: {e}{colors.END}")

    def export_html(self, output_file: str = "./output/uncommented_functions_report.html"):
        """生成 HTML 可视化报告(使用 Jinja2 模板)"""
        try:
            # 准备模板数据
            summary = self.data.get("summary", {})
            by_severity = self.data.get("by_severity", {})
            by_type = self.data.get("by_type", {})
            
            # 使用缓存的项目函数统计数据
            project_function_count = self.project_function_count
            
            # 准备严重程度图表数据
            severity_labels = list(by_severity.keys())
            severity_data = list(by_severity.values())
            severity_color_map = {
                'critical': '#dc2626',
                'high': '#ef4444',
                'medium': '#f59e0b',
                'low': '#10b981',
                'info': '#3b82f6'
            }
            severity_colors = [severity_color_map.get(s.lower(), '#6b7280') for s in severity_labels]
            
            # 准备类型图表数据
            type_items = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:Config.TOP_TYPES_DISPLAY]
            type_labels = [item[0] for item in type_items]
            type_data = [item[1] for item in type_items]
            
            # 准备项目排名数据
            project_rankings = [(i, (repo_id, count)) 
                              for i, (repo_id, count) in enumerate(project_function_count.most_common(20), 1)]
            
            # 设置 Jinja2 环境
            template_dir = Path(__file__).parent / 'templates'
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('report.html')
            
            # 渲染模板
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
            
            # 确保输出目录存在
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"\n{colors.GREEN}✓ HTML 报告已生成{colors.END}")
            print(f"  文件路径: {colors.CYAN}{output_file}{colors.END}")
            print(f"  可在浏览器中打开查看可视化报告")
        
        except Exception as e:
            print(f"\n{colors.RED}✗ 生成 HTML 报告失败: {e}{colors.END}")

    def run_full_analysis(self):
        """运行完整分析"""
        self.generate_summary_report()
        self.analyze_severity_distribution()
        self.analyze_type_distribution()
        self.analyze_rule_distribution()
        self.analyze_project_quality()
        self.analyze_cross_dimension()


class UncommentedFunctionsAnalyzer:
    """
    未注释函数分析器 - 高级接口
    整合数据采集和分析功能
    """

    def __init__(self, config: dict = None):
        """
        初始化分析器

        Args:
            config: 配置字典（可选）
        """
        self.config = config or {}
        self.data_analyzer = None
        self.classified_data = None

    def set_data(self, data: dict):
        """
        设置分析数据

        Args:
            data: 归类后的数据字典
        """
        self.classified_data = data
        self.data_analyzer = DataAnalyzer(data=data)

    def load_from_file(self, file_path: str = None):
        """
        从文件加载数据

        Args:
            file_path: 文件路径（可选，默认使用最新文件）
        """
        self.data_analyzer = DataAnalyzer(classified_file=file_path)
        self.classified_data = self.data_analyzer.data

    def analyze(self, export_formats: list = None):
        """
        执行分析

        Args:
            export_formats: 导出格式列表，可选 ['csv', 'html']
        """
        if not self.data_analyzer:
            print(f"{colors.YELLOW}⚠ 未设置数据，尝试加载最新数据文件...{colors.END}")
            self.load_from_file()

        # 运行完整分析
        self.data_analyzer.run_full_analysis()

        # 导出报告
        export_formats = export_formats or []
        if 'csv' in export_formats:
            self.data_analyzer.export_csv()
        if 'html' in export_formats:
            self.data_analyzer.export_html()

        return self.data_analyzer

    def get_summary(self) -> dict:
        """
        获取分析摘要

        Returns:
            分析摘要字典
        """
        if not self.classified_data:
            return {}

        return self.classified_data.get('summary', {})

    def export_csv(self, output_file: str = "./output/uncommented_functions_export.csv"):
        """导出 CSV 格式"""
        if not self.data_analyzer:
            print(f"{colors.RED}✗ 未初始化分析器{colors.END}")
            return
        self.data_analyzer.export_csv(output_file)

    def export_html(self, output_file: str = "./output/uncommented_functions_report.html"):
        """导出 HTML 格式"""
        if not self.data_analyzer:
            print(f"{colors.RED}✗ 未初始化分析器{colors.END}")
            return
        self.data_analyzer.export_html(output_file)

    def get_top_projects_by_uncommented_functions(self, top_n: int = 10) -> list:
        """
        获取未注释函数最多的项目

        Args:
            top_n: 返回前N个项目

        Returns:
            项目列表
        """
        if not self.classified_data:
            return []

        all_uncommented_functions = self.classified_data.get("all_uncommented_functions", [])
        project_function_count = Counter()

        for func in all_uncommented_functions:
            repo_id = func.get("repo_id")
            if repo_id:
                project_function_count[repo_id] += 1

        return project_function_count.most_common(top_n)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Merico 未注释函数数据分析器 - 美化版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python analyze_data.py                    # 分析最新数据并显示报告
  python analyze_data.py --export-csv       # 导出 CSV 格式
  python analyze_data.py --export-html      # 生成 HTML 可视化报告
  python analyze_data.py --all              # 生成所有格式报告
  python analyze_data.py --no-color         # 禁用彩色输出
        """
    )
    parser.add_argument(
        'file',
        type=str,
        nargs='?',
        help='归类数据文件路径'
    )
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='导出为 CSV 格式'
    )
    parser.add_argument(
        '--export-html',
        action='store_true',
        help='生成 HTML 可视化报告'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='生成所有格式的报告（CSV + HTML）'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='禁用彩色输出（适用于不支持 ANSI 的终端）'
    )

    args = parser.parse_args()

    # 禁用颜色
    global colors
    if args.no_color:
        colors = ColorScheme.no_color()

    # 查找最新的归类数据文件
    if not args.file:
        files = list(Path('./output').glob('classified_results_*.json'))
        if not files:
            print(f"{colors.RED}错误: 未找到归类数据文件{colors.END}")
            print("请先运行 merico_agent_advanced.py 生成数据")
            sys.exit(1)

        # 使用最新的文件
        args.file = str(max(files, key=lambda p: p.stat().st_mtime))
        print(f"{colors.CYAN}使用最新的数据文件: {colors.BOLD}{args.file}{colors.END}\n")

    # 创建分析器
    analyzer = DataAnalyzer(args.file)

    # 运行分析
    analyzer.run_full_analysis()

    # 导出报告
    if args.all:
        analyzer.export_csv()
        analyzer.export_html()
    else:
        if args.export_csv:
            analyzer.export_csv()
        if args.export_html:
            analyzer.export_html()

    # 结束提示
    print(f"\n{colors.GREEN}{colors.BOLD}✓ 分析完成！{colors.END}")
    if args.export_html or args.all:
        print(f"{colors.CYAN}💡 提示: 使用浏览器打开 uncommented_functions_report.html 查看可视化报告{colors.END}")


if __name__ == "__main__":
    main()
