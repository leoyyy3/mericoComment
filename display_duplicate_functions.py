"""
优化的重复函数展示工具
提供美化的控制台输出和HTML可视化报告
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any


class DuplicateFunctionsDisplay:
    """重复函数展示器"""

    def __init__(self, data_file: str = None, repo_name_file: str = "assets/repoId_repoName_list.json"):
        """
        初始化展示器
        
        Args:
            data_file: JSON数据文件路径，如果为None则使用最新的输出文件
            repo_name_file: 项目名称映射文件路径
        """
        self.data_file = data_file or self._get_latest_output_file()
        self.repo_name_map = self._load_repo_names(repo_name_file)
        self.data = self._load_data()
        self.stats = self._calculate_statistics()

    def _get_latest_output_file(self) -> str:
        """获取最新的输出文件"""
        output_dir = Path("output")
        if not output_dir.exists():
            raise FileNotFoundError("输出目录不存在")
        
        json_files = list(output_dir.glob("duplicate_functions_*.json"))
        if not json_files:
            raise FileNotFoundError("未找到数据文件")
        
        # 按修改时间排序，返回最新的
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        return str(latest_file)

    def _load_repo_names(self, repo_name_file: str) -> Dict[str, str]:
        """加载项目名称映射"""
        try:
            with open(repo_name_file, 'r', encoding='utf-8') as f:
                repo_list = json.load(f)
                return {item['repoId']: item['repoName'] for item in repo_list}
        except FileNotFoundError:
            print(f"⚠️  项目名称映射文件未找到: {repo_name_file}")
            return {}
    
    def _load_data(self) -> List[Dict]:
        """加载数据文件"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_project_name(self, repo_id: str) -> str:
        """获取项目名称,如果找不到则返回ID的缩写"""
        if repo_id in self.repo_name_map:
            return self.repo_name_map[repo_id]
        # 如果找不到,返回缩写的ID
        if len(repo_id) > 20:
            return f"{repo_id[:8]}...{repo_id[-4:]}"
        return repo_id
    
    def delete_duplicates(self):
        """删除output目录下duplicate_functions_*.*文件"""
        for file in Path("output").glob("duplicate_functions_*.*"):
            file.unlink()
            print(f"已删除: {file}")
        
        print("\n已删除所有重复函数文件")
        

    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {
            'total_projects': len(self.data),
            'projects_with_duplicates': 0,
            'total_duplicate_groups': 0,
            'total_duplicate_functions': 0,
            'total_files_affected': 0,
            'total_authors': set(),
            'language_distribution': defaultdict(int),
            'complexity_distribution': defaultdict(int),
            'top_duplicates': [],
            'projects_summary': []
        }

        all_groups = []

        for project in self.data:
            if not project.get('data'):
                continue

            project_data = project['data']
            if project_data.get('total', 0) > 0:
                stats['projects_with_duplicates'] += 1

            groups = project_data.get('data', [])
            stats['total_duplicate_groups'] += len(groups)

            for group in groups:
                # 添加项目ID到组信息中
                group['project_id'] = project['repo_id']
                all_groups.append(group)

                # 统计函数数量
                num_functions = group.get('numFunctions', 0)
                stats['total_duplicate_functions'] += num_functions

                # 统计文件数
                num_files = group.get('numFiles', 0)
                stats['total_files_affected'] += num_files

                # 统计作者
                emails = group.get('emails', [])
                stats['total_authors'].update(emails)

                # 语言分布
                language = group.get('language', 'Unknown')
                stats['language_distribution'][language] += num_functions

                # 复杂度分布
                complexity = group.get('maxComplexity', 0)
                if complexity <= 3:
                    stats['complexity_distribution']['低 (1-3)'] += 1
                elif complexity <= 7:
                    stats['complexity_distribution']['中 (4-7)'] += 1
                else:
                    stats['complexity_distribution']['高 (8+)'] += 1

            # 项目摘要
            if groups:
                stats['projects_summary'].append({
                    'repo_id': project['repo_id'],
                    'total_groups': len(groups),
                    'total_functions': sum(g.get('numFunctions', 0) for g in groups),
                    'total_files': sum(g.get('numFiles', 0) for g in groups)
                })

        # Top重复函数（按函数数量排序）
        stats['top_duplicates'] = sorted(
            all_groups,
            key=lambda x: x.get('numFunctions', 0),
            reverse=True
        )[:20]

        stats['total_authors'] = len(stats['total_authors'])

        return stats

    def display_console(self):
        """在控制台显示美化的输出"""
        print("\n" + "=" * 80)
        print(f"{'重复函数分析报告':^80}")
        print(f"{'生成时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^80}")
        print("=" * 80)

        # 总体统计
        print("\n📊 总体统计")
        print("-" * 80)
        print(f"  分析项目数:        {self.stats['total_projects']}")
        print(f"  有重复的项目:      {self.stats['projects_with_duplicates']}")
        print(f"  重复函数组数:      {self.stats['total_duplicate_groups']}")
        print(f"  重复函数总数:      {self.stats['total_duplicate_functions']}")
        print(f"  涉及文件数:        {self.stats['total_files_affected']}")
        print(f"  涉及作者数:        {self.stats['total_authors']}")

        # 语言分布
        if self.stats['language_distribution']:
            print("\n📝 语言分布")
            print("-" * 80)
            for lang, count in sorted(
                self.stats['language_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                bar = "█" * min(50, count)
                print(f"  {lang:15} {count:4} {bar}")

        # 复杂度分布
        if self.stats['complexity_distribution']:
            print("\n⚡ 复杂度分布")
            print("-" * 80)
            for complexity, count in sorted(self.stats['complexity_distribution'].items()):
                bar = "█" * min(50, count * 5)
                print(f"  {complexity:15} {count:4} {bar}")

        # Top重复函数
        if self.stats['top_duplicates']:
            print("\n🔥 Top 10 重复函数")
            print("-" * 110)
            print(f"{'排名':<6} {'项目名称':<45} {'函数名':<30} {'重复数':<8} {'文件数':<8} {'复杂度':<8}")
            print("-" * 110)
            
            for idx, group in enumerate(self.stats['top_duplicates'][:10], 1):
                project_id = group.get('project_id', 'Unknown')
                project_name = self._get_project_name(project_id)
                if len(project_name) > 43:
                    project_name = project_name[:40] + "..."
                
                func_name = group.get('groupName', 'Unknown')
                if len(func_name) > 28:
                    func_name = func_name[:25] + "..."
                
                num_funcs = group.get('numFunctions', 0)
                num_files = group.get('numFiles', 0)
                complexity = group.get('maxComplexity', 0)
                
                print(f"{idx:<6} {project_name:<45} {func_name:<30} {num_funcs:<8} {num_files:<8} {complexity:<8}")

        # 项目摘要
        if self.stats['projects_summary']:
            print("\n📁 项目摘要 (有重复的项目)")
            print("-" * 80)
            print(f"{'项目ID':<40} {'组数':<8} {'函数数':<10} {'文件数':<10}")
            print("-" * 80)
            
            for project in sorted(
                self.stats['projects_summary'],
                key=lambda x: x['total_functions'],
                reverse=True
            )[:10]:
                repo_id = project['repo_id']
                if len(repo_id) > 38:
                    repo_id = repo_id[:35] + "..."
                
                print(f"{repo_id:<40} {project['total_groups']:<8} "
                      f"{project['total_functions']:<10} {project['total_files']:<10}")

        print("\n" + "=" * 80)
        print(f"数据文件: {self.data_file}")
        print("=" * 80 + "\n")

    def generate_html_report(self, output_file: str = None):
        """生成HTML报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/duplicate_functions_report_{timestamp}.html"

        html_content = self._generate_html_content()
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)

        self.delete_duplicates()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        
        
        print(f"✅ HTML报告已生成: {output_path.absolute()}")
        return str(output_path.absolute())

    def _generate_html_content(self) -> str:
        """生成HTML内容"""
        # 准备图表数据
        language_labels = list(self.stats['language_distribution'].keys())
        language_data = list(self.stats['language_distribution'].values())
        
        complexity_labels = list(self.stats['complexity_distribution'].keys())
        complexity_data = list(self.stats['complexity_distribution'].values())
        
        # 准备项目柱状图数据
        project_chart_labels = []
        project_chart_data = []
        for project in sorted(self.stats['projects_summary'], key=lambda x: x['total_functions'], reverse=True)[:10]:
            project_name = self._get_project_name(project['repo_id'])
            # 简化项目名称显示
            if '/' in project_name:
                project_name = project_name.split('/')[-1].replace('_src', '')
            project_chart_labels.append(project_name)
            project_chart_data.append(project['total_functions'])

        # 准备表格数据
        table_rows = ""
        for idx, group in enumerate(self.stats['top_duplicates'], 1):
            project_id = group.get('project_id', 'Unknown')
            project_name = self._get_project_name(project_id)
            
            files_list = "<br>".join(group.get('filePaths', [])[:5])
            if len(group.get('filePaths', [])) > 5:
                files_list += f"<br>... 还有 {len(group['filePaths']) - 5} 个文件"
            
            emails_list = "<br>".join(group.get('emails', []))
            
            table_rows += f"""
            <tr>
                <td>{idx}</td>
                <td><small title="{project_id}">{project_name}</small></td>
                <td><code>{group.get('groupName', 'Unknown')}</code></td>
                <td>{group.get('language', 'Unknown')}</td>
                <td>{group.get('numFunctions', 0)}</td>
                <td>{group.get('numFiles', 0)}</td>
                <td>{group.get('maxComplexity', 0)}</td>
                <td>{group.get('avgLines', 0):.1f}</td>
                <td><small>{files_list}</small></td>
                <td><small>{emails_list}</small></td>
            </tr>
            """

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>重复函数分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
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
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.95em;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 25px;
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .chart-container h3 {{
            margin-bottom: 15px;
            color: #555;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
            font-size: 0.9em;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 0.85em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 重复函数分析报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{self.stats['total_projects']}</div>
                <div class="label">分析项目数</div>
            </div>
            <div class="stat-card">
                <div class="number">{self.stats['projects_with_duplicates']}</div>
                <div class="label">有重复的项目</div>
            </div>
            <div class="stat-card">
                <div class="number">{self.stats['total_duplicate_groups']}</div>
                <div class="label">重复函数组数</div>
            </div>
            <div class="stat-card">
                <div class="number">{self.stats['total_duplicate_functions']}</div>
                <div class="label">重复函数总数</div>
            </div>
            <div class="stat-card">
                <div class="number">{self.stats['total_files_affected']}</div>
                <div class="label">涉及文件数</div>
            </div>
            <div class="stat-card">
                <div class="number">{self.stats['total_authors']}</div>
                <div class="label">涉及作者数</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 数据分布</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <h3>语言分布</h3>
                    <canvas id="languageChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>复杂度分布</h3>
                    <canvas id="complexityChart"></canvas>
                </div>
            </div>
            <div class="chart-container" style="margin-top: 30px;">
                <h3>项目重复函数分布 (Top 10)</h3>
                <canvas id="projectChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>🔥 Top 重复函数详情</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>项目名称</th>
                            <th>函数名</th>
                            <th>语言</th>
                            <th>重复数</th>
                            <th>文件数</th>
                            <th>复杂度</th>
                            <th>平均行数</th>
                            <th>涉及文件</th>
                            <th>涉及作者</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>数据来源: {self.data_file}</p>
            <p>Merico 重复函数分析工具 © 2025</p>
        </div>
    </div>
    
    <script>
        // 语言分布图表
        const languageCtx = document.getElementById('languageChart').getContext('2d');
        new Chart(languageCtx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(language_labels)},
                datasets: [{{
                    data: {json.dumps(language_data)},
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe',
                        '#43e97b',
                        '#fa709a',
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // 复杂度分布图表
        const complexityCtx = document.getElementById('complexityChart').getContext('2d');
        new Chart(complexityCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(complexity_labels)},
                datasets: [{{
                    label: '函数组数',
                    data: {json.dumps(complexity_data)},
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        // 项目分布图表
        const projectCtx = document.getElementById('projectChart').getContext('2d');
        new Chart(projectCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(project_chart_labels)},
                datasets: [{{
                    label: '重复函数数量',
                    data: {json.dumps(project_chart_data)},
                    backgroundColor: '#764ba2',
                    borderColor: '#667eea',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: '重复函数数量'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: '项目名称'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        return html

    def export_csv(self, output_file: str = None):
        """导出为CSV格式"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/duplicate_functions_{timestamp}.csv"

        import csv
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '排名', '项目ID', '项目名称', '函数名', '语言', '重复数', '文件数', 
                '复杂度', '平均行数', '涉及文件', '涉及作者'
            ])
            
            # 写入数据
            for idx, group in enumerate(self.stats['top_duplicates'], 1):
                project_id = group.get('project_id', 'Unknown')
                project_name = self._get_project_name(project_id)
                writer.writerow([
                    idx,
                    project_id,
                    project_name,
                    group.get('groupName', 'Unknown'),
                    group.get('language', 'Unknown'),
                    group.get('numFunctions', 0),
                    group.get('numFiles', 0),
                    group.get('maxComplexity', 0),
                    f"{group.get('avgLines', 0):.1f}",
                    '; '.join(group.get('filePaths', [])),
                    '; '.join(group.get('emails', []))
                ])
        
        print(f"✅ CSV文件已导出: {output_path.absolute()}")
        return str(output_path.absolute())


def main():
    """主函数"""
    import sys
    
    # 解析命令行参数
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        display = DuplicateFunctionsDisplay(data_file)
        
        # 显示控制台输出
        display.display_console()
        
        # 生成HTML报告
        html_file = display.generate_html_report()
        
        # 导出CSV
        # csv_file = display.export_csv()
        
        # print("\n✨ 所有报告已生成完成!")
        print(f"   HTML报告: {html_file}")
        # print(f"   CSV导出:  {csv_file}")
        
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
