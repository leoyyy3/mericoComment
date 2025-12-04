"""
按项目和文件查看未注释函数
提供详细的未注释函数信息，按项目和文件组织
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


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
        """禁用颜色"""
        Colors.HEADER = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''
        Colors.END = ''


def load_classified_data(file_path):
    """加载分类数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}加载数据失败: {e}{Colors.END}")
        sys.exit(1)


def organize_by_project_and_file(functions):
    """按项目和文件组织函数"""
    organized = defaultdict(lambda: defaultdict(list))

    for func in functions:
        repo_id = func.get("repo_id", "unknown")
        file_path = func.get("file_path", "unknown")
        organized[repo_id][file_path].append(func)

    return organized


def get_project_name(repo_id, by_project_data):
    """获取项目名称（从git_url提取）"""
    if repo_id in by_project_data:
        project_data = by_project_data[repo_id].get("data", {})
        if "data" in project_data and len(project_data["data"]) > 0:
            git_url = project_data["data"][0].get("git_url", "")
            if git_url:
                # 从 git@code.idc.hexun.com:tech_wzkf/project_src.git 提取 project_src
                parts = git_url.split("/")
                if parts:
                    return parts[-1].replace(".git", "")
    return repo_id[:8]  # 返回项目ID的前8位


def format_complexity(cyclomatic):
    """格式化复杂度显示"""
    if cyclomatic >= 10:
        return f"{Colors.RED}高({cyclomatic}){Colors.END}"
    elif cyclomatic >= 5:
        return f"{Colors.YELLOW}中({cyclomatic}){Colors.END}"
    else:
        return f"{Colors.GREEN}低({cyclomatic}){Colors.END}"


def format_date(date_str):
    """格式化日期"""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def print_function_detail(func, index):
    """打印函数详细信息"""
    name = func.get("name", "unknown")
    params = func.get("params", "")
    start_line = func.get("start_line", "?")
    end_line = func.get("end_line", "?")
    cyclomatic = func.get("cyclomatic", 0)
    language = func.get("language", "unknown")
    author_name = func.get("frequentAuthorName", "unknown")
    author_email = func.get("frequentAuthorEmail", "unknown")
    latest_time = func.get("latest_author_time", "unknown")

    # 函数签名
    print(f"    {Colors.BOLD}{index}.{Colors.END} {Colors.CYAN}{name}{params}{Colors.END}")

    # 位置信息
    print(f"       📍 位置: 第 {Colors.YELLOW}{start_line}{Colors.END} - {Colors.YELLOW}{end_line}{Colors.END} 行")

    # 语言和复杂度
    complexity_str = format_complexity(cyclomatic)
    print(f"       🔧 语言: {Colors.BLUE}{language}{Colors.END}  |  复杂度: {complexity_str}")

    # 作者信息
    print(f"       👤 作者: {Colors.GREEN}{author_name}{Colors.END} ({author_email})")

    # 最后修改时间
    formatted_time = format_date(latest_time)
    print(f"       ⏰ 最后修改: {formatted_time}")

    print()


def print_project_summary(repo_id, files_data, by_project_data):
    """打印项目摘要"""
    project_name = get_project_name(repo_id, by_project_data)
    total_functions = sum(len(funcs) for funcs in files_data.values())
    total_files = len(files_data)

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}📦 项目: {project_name}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"{Colors.CYAN}项目ID:{Colors.END} {repo_id}")
    print(f"{Colors.CYAN}未注释函数数:{Colors.END} {Colors.RED}{total_functions}{Colors.END}")
    print(f"{Colors.CYAN}涉及文件数:{Colors.END} {Colors.YELLOW}{total_files}{Colors.END}")
    print()


def print_file_section(file_path, functions):
    """打印文件部分"""
    print(f"  {Colors.BOLD}{Colors.BLUE}📄 {file_path}{Colors.END}")
    print(f"  {Colors.CYAN}{'─' * 76}{Colors.END}")
    print(f"  {Colors.YELLOW}未注释函数数: {len(functions)}{Colors.END}\n")

    for idx, func in enumerate(functions, 1):
        print_function_detail(func, idx)


def export_markdown(organized_data, by_project_data, output_file="./output/uncommented_functions_detail.md"):
    """导出为Markdown格式"""
    lines = []

    lines.append("# 未注释函数详细报告\n")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("---\n")

    # 统计信息
    total_projects = len(organized_data)
    total_functions = sum(
        len(funcs)
        for files_data in organized_data.values()
        for funcs in files_data.values()
    )
    total_files = sum(len(files_data) for files_data in organized_data.values())

    lines.append("## 📊 总体统计\n")
    lines.append(f"- **项目总数**: {total_projects}\n")
    lines.append(f"- **文件总数**: {total_files}\n")
    lines.append(f"- **未注释函数总数**: {total_functions}\n")
    lines.append("\n---\n")

    # 按项目详细信息
    for repo_id, files_data in sorted(organized_data.items()):
        project_name = get_project_name(repo_id, by_project_data)
        total_funcs = sum(len(funcs) for funcs in files_data.values())

        lines.append(f"\n## 📦 项目: {project_name}\n")
        lines.append(f"- **项目ID**: `{repo_id}`\n")
        lines.append(f"- **未注释函数数**: {total_funcs}\n")
        lines.append(f"- **涉及文件数**: {len(files_data)}\n")
        lines.append("\n")

        for file_path, functions in sorted(files_data.items()):
            lines.append(f"### 📄 {file_path}\n")
            lines.append(f"**未注释函数数**: {len(functions)}\n\n")

            for idx, func in enumerate(functions, 1):
                name = func.get("name", "unknown")
                params = func.get("params", "")
                start_line = func.get("start_line", "?")
                end_line = func.get("end_line", "?")
                cyclomatic = func.get("cyclomatic", 0)
                language = func.get("language", "unknown")
                author_name = func.get("frequentAuthorName", "unknown")
                author_email = func.get("frequentAuthorEmail", "unknown")
                latest_time = func.get("latest_author_time", "unknown")
                formatted_time = format_date(latest_time)

                lines.append(f"#### {idx}. `{name}{params}`\n")
                lines.append(f"- **位置**: 第 {start_line}-{end_line} 行\n")
                lines.append(f"- **语言**: {language}\n")
                lines.append(f"- **复杂度**: {cyclomatic}\n")
                lines.append(f"- **作者**: {author_name} ({author_email})\n")
                lines.append(f"- **最后修改**: {formatted_time}\n")
                lines.append("\n")

            lines.append("\n")

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"\n{Colors.GREEN}✓ Markdown 报告已导出{Colors.END}")
    print(f"  文件路径: {Colors.CYAN}{output_file}{Colors.END}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='按项目和文件查看未注释函数',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python view_by_project_file.py                          # 查看所有未注释函数
  python view_by_project_file.py --export-markdown        # 导出为 Markdown
  python view_by_project_file.py --project <PROJECT_ID>  # 只查看指定项目
  python view_by_project_file.py --no-color               # 禁用彩色输出
        """
    )

    parser.add_argument(
        'file',
        type=str,
        nargs='?',
        help='分类数据文件路径'
    )

    parser.add_argument(
        '--export-markdown',
        action='store_true',
        help='导出为 Markdown 格式'
    )

    parser.add_argument(
        '--project',
        type=str,
        help='只显示指定项目的函数'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='禁用彩色输出'
    )

    args = parser.parse_args()

    # 禁用颜色
    if args.no_color:
        Colors.disable()

    # 查找最新的分类数据文件
    if not args.file:
        files = list(Path('./output').glob('classified_results_*.json'))
        if not files:
            print(f"{Colors.RED}错误: 未找到分类数据文件{Colors.END}")
            print("请先运行 reclassify_data.py 生成数据")
            sys.exit(1)

        args.file = str(max(files, key=lambda p: p.stat().st_mtime))
        print(f"{Colors.CYAN}使用最新的数据文件: {Colors.BOLD}{args.file}{Colors.END}\n")

    # 加载数据
    data = load_classified_data(args.file)

    all_functions = data.get("all_uncommented_functions", [])
    by_project = data.get("by_project", {})

    if not all_functions:
        print(f"{Colors.YELLOW}⚠ 没有找到未注释函数{Colors.END}")
        sys.exit(0)

    # 按项目和文件组织
    organized = organize_by_project_and_file(all_functions)

    # 如果指定了项目，只显示该项目
    if args.project:
        if args.project not in organized:
            print(f"{Colors.RED}错误: 未找到项目 {args.project}{Colors.END}")
            print(f"\n可用的项目ID:")
            for repo_id in organized.keys():
                project_name = get_project_name(repo_id, by_project)
                print(f"  - {repo_id} ({project_name})")
            sys.exit(1)

        organized = {args.project: organized[args.project]}

    # 导出 Markdown
    if args.export_markdown:
        export_markdown(organized, by_project)
        return

    # 打印报告头
    width = 80
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * width}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'未注释函数详细报告 - 按项目和文件查看'.center(width)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * width}{Colors.END}")

    # 统计信息
    total_projects = len(organized)
    total_functions = sum(
        len(funcs)
        for files_data in organized.values()
        for funcs in files_data.values()
    )
    total_files = sum(len(files_data) for files_data in organized.values())

    print(f"\n{Colors.CYAN}⏰ 生成时间:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.CYAN}📁 项目总数:{Colors.END} {total_projects}")
    print(f"{Colors.CYAN}📄 文件总数:{Colors.END} {total_files}")
    print(f"{Colors.CYAN}📝 函数总数:{Colors.END} {Colors.RED}{total_functions}{Colors.END}")

    # 按项目打印
    for repo_id, files_data in sorted(organized.items()):
        print_project_summary(repo_id, files_data, by_project)

        # 按文件打印
        for file_path, functions in sorted(files_data.items()):
            print_file_section(file_path, functions)

    # 结束提示
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * width}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✓ 报告生成完成！{Colors.END}")
    print(f"\n{Colors.CYAN}💡 提示:{Colors.END}")
    print(f"  - 使用 {Colors.YELLOW}--export-markdown{Colors.END} 导出为 Markdown 文件")
    print(f"  - 使用 {Colors.YELLOW}--project <PROJECT_ID>{Colors.END} 查看指定项目")
    print(f"\n")


if __name__ == "__main__":
    main()
