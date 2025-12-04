"""
未注释函数分析器 - 分析项目中未添加文档注释的函数
提供深入的统计分析和可视化报告
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


class Colors:
    """终端颜色配置"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @staticmethod
    def disable():
        """禁用颜色（适用于不支持ANSI的终端）"""
        Colors.HEADER = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''
        Colors.END = ''


class DataAnalyzer:
    """未注释函数数据分析器"""

    def __init__(self, classified_file: str):
        """
        初始化分析器

        Args:
            classified_file: 归类数据文件路径
        """
        self.classified_file = classified_file
        self.data = self.load_data()

    def load_data(self):
        """加载数据"""
        try:
            with open(self.classified_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载数据失败: {e}")
            sys.exit(1)

    @staticmethod
    def print_section_header(title: str):
        """打印美化的章节标题"""
        width = 80
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * width}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title.center(width)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * width}{Colors.END}\n")

    @staticmethod
    def print_subsection(title: str):
        """打印美化的小节标题"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 78}{Colors.END}")

    @staticmethod
    def print_bar_chart(label: str, value: int, total: int, width: int = 40, color: str = Colors.GREEN):
        """打印美化的条形图"""
        percentage = (value / total * 100) if total > 0 else 0
        filled = int(percentage / 100 * width)
        bar = '█' * filled + '░' * (width - filled)

        print(f"{label:30s} │ {color}{bar}{Colors.END} │ {Colors.BOLD}{value:6d}{Colors.END} ({percentage:5.1f}%)")

    @staticmethod
    def get_severity_color(severity: str) -> str:
        """根据严重程度返回颜色"""
        severity_colors = {
            'critical': Colors.RED,
            'high': Colors.RED,
            'medium': Colors.YELLOW,
            'low': Colors.GREEN,
            'info': Colors.CYAN,
        }
        return severity_colors.get(severity.lower(), Colors.END)

    def analyze_severity_distribution(self):
        """分析严重程度分布"""
        self.print_section_header("复杂度分布分析")

        by_severity = self.data.get("by_severity", {})
        total = sum(by_severity.values())

        if total == 0:
            print(f"{Colors.YELLOW}⚠ 无数据{Colors.END}")
            return

        # 排序并计算百分比
        sorted_severity = sorted(by_severity.items(), key=lambda x: x[1], reverse=True)

        for severity, count in sorted_severity:
            color = self.get_severity_color(severity)
            self.print_bar_chart(severity, count, total, color=color)

        print(f"\n{Colors.BOLD}总计: {total:,} 个未注释函数{Colors.END}")

    def analyze_type_distribution(self):
        """分析类型分布"""
        self.print_section_header("函数类型分布分析 (Top 20)")

        by_type = self.data.get("by_type", {})
        total = sum(by_type.values())

        if total == 0:
            print(f"{Colors.YELLOW}⚠ 无数据{Colors.END}")
            return

        # 排序并显示 Top 20
        sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:20]

        for i, (issue_type, count) in enumerate(sorted_types, 1):
            rank_color = Colors.YELLOW if i <= 3 else Colors.END
            label = f"{rank_color}{i:2d}.{Colors.END} {issue_type}"
            self.print_bar_chart(label, count, total, color=Colors.BLUE)

        print(f"\n{Colors.BOLD}统计信息:{Colors.END}")
        print(f"  • 总类型数: {Colors.CYAN}{len(by_type)}{Colors.END}")
        print(f"  • 未注释函数数: {Colors.CYAN}{total:,}{Colors.END}")

    def analyze_rule_distribution(self):
        """分析规则分布"""
        self.print_section_header("作者分布分析 (Top 20)")

        by_rule = self.data.get("by_rule", {})
        total = sum(by_rule.values())

        if total == 0:
            print(f"{Colors.YELLOW}⚠ 无数据{Colors.END}")
            return

        # 排序并显示 Top 20
        sorted_rules = sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:20]

        for i, (rule, count) in enumerate(sorted_rules, 1):
            rank_color = Colors.YELLOW if i <= 3 else Colors.END
            label = f"{rank_color}{i:2d}.{Colors.END} {rule[:35]}"
            self.print_bar_chart(label, count, total, color=Colors.CYAN)

        print(f"\n{Colors.BOLD}统计信息:{Colors.END}")
        print(f"  • 作者总数: {Colors.CYAN}{len(by_rule)}{Colors.END}")
        print(f"  • 未注释函数总数: {Colors.CYAN}{total:,}{Colors.END}")

    def analyze_project_quality(self):
        """分析各项目未注释函数情况"""
        self.print_section_header("项目未注释函数排名")

        by_project = self.data.get("by_project", {})
        all_uncommented_functions = self.data.get("all_uncommented_functions", [])

        # 统计每个项目的未注释函数数
        project_function_count = Counter()
        for func in all_uncommented_functions:
            repo_id = func.get("repo_id")
            if repo_id:
                project_function_count[repo_id] += 1

        if len(project_function_count) == 0:
            print(f"{Colors.YELLOW}⚠ 无有效项目数据{Colors.END}")
            return

        # 排序并显示 Top 20
        sorted_projects = project_function_count.most_common(20)

        self.print_subsection("未注释函数最多的项目 (Top 20)")
        print(f"\n{'排名':<6} {'项目ID':<45} {'未注释函数数':>12}")
        print(f"{Colors.CYAN}{'─' * 78}{Colors.END}")

        for i, (repo_id, count) in enumerate(sorted_projects, 1):
            if i <= 3:
                rank_icon = f"{Colors.RED}🔥{Colors.END}"
            elif i <= 10:
                rank_icon = f"{Colors.YELLOW}⚠️{Colors.END}"
            else:
                rank_icon = "  "

            print(f"{rank_icon} {i:2d}.  {repo_id:<45} {Colors.RED}{count:>8,}{Colors.END} 个")

        # 未注释函数最少的项目
        self.print_subsection("未注释函数最少的项目 (Top 10)")
        print(f"\n{'排名':<6} {'项目ID':<45} {'未注释函数数':>12}")
        print(f"{Colors.CYAN}{'─' * 78}{Colors.END}")

        least_functions = sorted(project_function_count.items(), key=lambda x: x[1])[:10]
        for i, (repo_id, count) in enumerate(least_functions, 1):
            icon = f"{Colors.GREEN}✓{Colors.END}"
            print(f"{icon} {i:2d}.  {repo_id:<45} {Colors.GREEN}{count:>8,}{Colors.END} 个")

        # 统计汇总
        avg_functions = sum(project_function_count.values()) / len(project_function_count)
        print(f"\n{Colors.BOLD}统计汇总:{Colors.END}")
        print(f"  • 项目总数: {Colors.CYAN}{len(project_function_count)}{Colors.END}")
        print(f"  • 平均未注释函数数: {Colors.CYAN}{avg_functions:.1f}{Colors.END}")
        print(f"  • 最大未注释函数数: {Colors.RED}{sorted_projects[0][1]:,}{Colors.END} ({sorted_projects[0][0][:30]}...)")
        print(f"  • 最小未注释函数数: {Colors.GREEN}{least_functions[0][1]:,}{Colors.END} ({least_functions[0][0][:30]}...)")

    def analyze_cross_dimension(self):
        """交叉维度分析"""
        self.print_section_header("交叉维度分析")

        all_uncommented_functions = self.data.get("all_uncommented_functions", [])

        if not all_uncommented_functions:
            print(f"{Colors.YELLOW}⚠ 无数据{Colors.END}")
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
            print(f"\n{color}{Colors.BOLD}{severity.upper()}{Colors.END}")
            types = severity_type[severity]
            sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (func_type, count) in enumerate(sorted_types, 1):
                print(f"  {i}. {func_type}: {Colors.BOLD}{count}{Colors.END}")

    def generate_summary_report(self):
        """生成总结报告"""
        summary = self.data.get("summary", {})

        # 打印标题
        width = 80
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * width}{Colors.END}")
        title = "📊 Merico 项目未注释函数分析总结报告"
        print(f"{Colors.BOLD}{Colors.HEADER}{title.center(width + 2)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * width}{Colors.END}\n")

        # 时间信息
        print(f"{Colors.CYAN}⏰ 分析时间:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 基本统计
        self.print_subsection("基本统计")
        total_projects = summary.get('total_projects', 0)
        successful_projects = summary.get('successful_projects', 0)
        failed_projects = summary.get('failed_projects', 0)
        total_uncommented_functions = summary.get('total_uncommented_functions', 0)

        print(f"\n  📁 总项目数: {Colors.BOLD}{Colors.CYAN}{total_projects}{Colors.END}")
        print(f"  ✓ 成功项目数: {Colors.BOLD}{Colors.GREEN}{successful_projects}{Colors.END}")
        print(f"  ✗ 失败项目数: {Colors.BOLD}{Colors.RED}{failed_projects}{Colors.END}")
        print(f"  📝 总未注释函数数: {Colors.BOLD}{Colors.YELLOW}{total_uncommented_functions:,}{Colors.END}")

        if successful_projects > 0:
            avg_functions = total_uncommented_functions / successful_projects
            print(f"  📈 平均每项目未注释函数数: {Colors.BOLD}{Colors.CYAN}{avg_functions:.1f}{Colors.END}")

        # 数据质量评估
        if total_projects > 0:
            success_rate = (successful_projects / total_projects) * 100
            if success_rate >= 90:
                rate_color = Colors.GREEN
                rate_icon = "✓"
            elif success_rate >= 70:
                rate_color = Colors.YELLOW
                rate_icon = "⚠"
            else:
                rate_color = Colors.RED
                rate_icon = "✗"

            print(f"\n  {rate_icon} 数据获取成功率: {rate_color}{Colors.BOLD}{success_rate:.1f}%{Colors.END}")

        # 失败项目列表
        errors = self.data.get("errors", [])
        if errors:
            self.print_subsection(f"失败的项目 ({len(errors)})")
            print()
            for i, error in enumerate(errors[:10], 1):
                print(f"  {Colors.RED}✗{Colors.END} {i:2d}. {error.get('repo_id', 'Unknown')[:50]}")
                print(f"       {Colors.YELLOW}原因: {error.get('error', 'Unknown error')}{Colors.END}")
            if len(errors) > 10:
                print(f"\n  {Colors.CYAN}... 还有 {len(errors) - 10} 个失败项目{Colors.END}")

    def export_csv(self, output_file: str = "uncommented_functions_export.csv"):
        """导出为 CSV 格式"""
        try:
            import csv

            all_uncommented_functions = self.data.get("all_uncommented_functions", [])

            if not all_uncommented_functions:
                print(f"\n{Colors.YELLOW}⚠ 无数据可导出{Colors.END}")
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

            print(f"\n{Colors.GREEN}✓ 未注释函数数据已导出{Colors.END}")
            print(f"  文件路径: {Colors.CYAN}{output_file}{Colors.END}")
            print(f"  总记录数: {Colors.BOLD}{len(all_uncommented_functions):,}{Colors.END}")

        except Exception as e:
            print(f"\n{Colors.RED}✗ 导出 CSV 失败: {e}{Colors.END}")

    def export_html(self, output_file: str = "uncommented_functions_report.html"):
        """生成 HTML 可视化报告"""
        try:
            summary = self.data.get("summary", {})
            by_severity = self.data.get("by_severity", {})
            by_type = self.data.get("by_type", {})
            by_rule = self.data.get("by_rule", {})
            all_uncommented_functions = self.data.get("all_uncommented_functions", [])

            # 统计项目未注释函数情况
            project_function_count = Counter()
            for func in all_uncommented_functions:
                repo_id = func.get("repo_id")
                if repo_id:
                    project_function_count[repo_id] += 1

            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merico 项目未注释函数分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        .card-title {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .card-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .card.success .card-value {{ color: #10b981; }}
        .card.warning .card-value {{ color: #f59e0b; }}
        .card.danger .card-value {{ color: #ef4444; }}
        .section {{
            margin-bottom: 50px;
        }}
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            color: #333;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
        }}
        .table-container {{
            overflow-x: auto;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:hover {{
            background: #f3f4f6;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge.critical {{ background: #fee2e2; color: #dc2626; }}
        .badge.high {{ background: #fef3c7; color: #d97706; }}
        .badge.medium {{ background: #dbeafe; color: #2563eb; }}
        .badge.low {{ background: #d1fae5; color: #059669; }}
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}
        .rank-icon {{
            font-size: 1.2em;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Merico 项目未注释函数分析报告</h1>
            <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>

        <div class="content">
            <!-- 汇总卡片 -->
            <div class="summary-cards">
                <div class="card">
                    <div class="card-title">📁 总项目数</div>
                    <div class="card-value">{summary.get('total_projects', 0)}</div>
                </div>
                <div class="card success">
                    <div class="card-title">✓ 成功项目</div>
                    <div class="card-value">{summary.get('successful_projects', 0)}</div>
                </div>
                <div class="card danger">
                    <div class="card-title">✗ 失败项目</div>
                    <div class="card-value">{summary.get('failed_projects', 0)}</div>
                </div>
                <div class="card warning">
                    <div class="card-title">📝 总未注释函数数</div>
                    <div class="card-value">{summary.get('total_uncommented_functions', 0):,}</div>
                </div>
            </div>

            <!-- 严重程度分布图表 -->
            <div class="section">
                <h2 class="section-title">复杂度分布</h2>
                <div class="chart-container">
                    <canvas id="severityChart"></canvas>
                </div>
            </div>

            <!-- 问题类型分布图表 -->
            <div class="section">
                <h2 class="section-title">函数类型分布 (Top 15)</h2>
                <div class="chart-container">
                    <canvas id="typeChart"></canvas>
                </div>
            </div>

            <!-- 项目质量排名表格 -->
            <div class="section">
                <h2 class="section-title">项目未注释函数排名 (Top 20)</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>项目ID</th>
                                <th>未注释函数数</th>
                                <th>状态</th>
                            </tr>
                        </thead>
                        <tbody>
"""

            # 添加项目排名数据
            sorted_projects = project_function_count.most_common(20)
            for i, (repo_id, count) in enumerate(sorted_projects, 1):
                icon = "🔥" if i <= 3 else ("⚠️" if i <= 10 else "")
                status_class = "critical" if i <= 3 else ("high" if i <= 10 else "medium")
                html_content += f"""
                            <tr>
                                <td><span class="rank-icon">{icon}</span>{i}</td>
                                <td style="font-family: monospace; font-size: 0.9em;">{repo_id}</td>
                                <td><strong>{count:,}</strong></td>
                                <td><span class="badge {status_class}">需关注</span></td>
                            </tr>
"""

            html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Merico 项目未注释函数分析系统 | 自动生成报告</p>
        </div>
    </div>

    <script>
"""

            # 生成图表数据
            severity_labels = list(by_severity.keys())
            severity_data = list(by_severity.values())
            severity_colors = {
                'critical': '#dc2626',
                'high': '#ef4444',
                'medium': '#f59e0b',
                'low': '#10b981',
                'info': '#3b82f6'
            }
            severity_bg_colors = [severity_colors.get(s.lower(), '#6b7280') for s in severity_labels]

            type_items = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:15]
            type_labels = [item[0] for item in type_items]
            type_data = [item[1] for item in type_items]

            html_content += f"""
        // 严重程度图表
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        new Chart(severityCtx, {{
            type: 'doughnut',
            data: {{
                labels: {severity_labels},
                datasets: [{{
                    data: {severity_data},
                    backgroundColor: {severity_bg_colors},
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{ size: 14 }},
                            padding: 15
                        }}
                    }},
                    title: {{
                        display: false
                    }}
                }}
            }}
        }});

        // 问题类型图表
        const typeCtx = document.getElementById('typeChart').getContext('2d');
        new Chart(typeCtx, {{
            type: 'bar',
            data: {{
                labels: {type_labels},
                datasets: [{{
                    label: '未注释函数数量',
                    data: {type_data},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            font: {{ size: 12 }}
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{ size: 11 }},
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"\n{Colors.GREEN}✓ HTML 报告已生成{Colors.END}")
            print(f"  文件路径: {Colors.CYAN}{output_file}{Colors.END}")
            print(f"  可在浏览器中打开查看可视化报告")

        except Exception as e:
            print(f"\n{Colors.RED}✗ 生成 HTML 报告失败: {e}{Colors.END}")

    def run_full_analysis(self):
        """运行完整分析"""
        self.generate_summary_report()
        self.analyze_severity_distribution()
        self.analyze_type_distribution()
        self.analyze_rule_distribution()
        self.analyze_project_quality()
        self.analyze_cross_dimension()


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
    if args.no_color:
        Colors.disable()

    # 查找最新的归类数据文件
    if not args.file:
        files = list(Path('./output').glob('classified_results_*.json'))
        if not files:
            print(f"{Colors.RED}错误: 未找到归类数据文件{Colors.END}")
            print("请先运行 merico_agent_advanced.py 生成数据")
            sys.exit(1)

        # 使用最新的文件
        args.file = str(max(files, key=lambda p: p.stat().st_mtime))
        print(f"{Colors.CYAN}使用最新的数据文件: {Colors.BOLD}{args.file}{Colors.END}\n")

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
    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 分析完成！{Colors.END}")
    if args.export_html or args.all:
        print(f"{Colors.CYAN}💡 提示: 使用浏览器打开 uncommented_functions_report.html 查看可视化报告{Colors.END}")


if __name__ == "__main__":
    main()
