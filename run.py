#!/usr/bin/env python3
"""
Merico 代码质量分析系统 - 统一入口

使用方法:
    # 启动 Web 服务
    python run.py serve --port 8080

    # 运行分析
    python run.py analyze --type all

    # 生成周报
    python run.py weekly --entity-id xxx --workspace-id xxx

    # 单独运行分析器
    python run.py data-analyze --file output/classified_results_xxx.json
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def cmd_serve(args):
    """启动 Web 服务"""
    from src.api import create_app

    app = create_app(args.config)

    print(f"🚀 启动服务: http://{args.host}:{args.port}")
    print(f"📖 API 文档:")
    print(f"   - 健康检查: GET  /api/health")
    print(f"   - 服务状态: GET  /api/status")
    print(f"   - 分析报告: GET  /api/analysis/reports")
    print(f"   - 运行分析: POST /api/analysis/all/run")
    print(f"   - 生成周报: POST /api/weekly-report/generate")

    app.run(host=args.host, port=args.port, debug=args.debug)


def cmd_analyze(args):
    """运行代码分析"""
    from config import ConfigLoader
    from src.services import AnalysisService

    # 加载配置
    loader = ConfigLoader(args.config)
    settings = loader.load()

    # 创建服务
    service = AnalysisService(settings)

    # 运行分析
    if args.type == 'all':
        result = service.run_all()
    elif args.type == 'uncommented':
        result = service.run_uncommented_analysis()
    elif args.type == 'duplicate':
        result = service.run_duplicate_analysis()
    else:
        print(f"未知的分析类型: {args.type}")
        sys.exit(1)

    print(f"\n✅ 分析完成!")
    print(f"结果: {result}")


def cmd_data_analyze(args):
    """分析已有数据文件"""
    from src.core.analyzers import DataAnalyzer

    analyzer = DataAnalyzer(classified_file=args.file)
    analyzer.run_full_analysis()

    if args.export_csv:
        analyzer.export_csv()
    if args.export_html:
        analyzer.export_html()

    print(f"\n✅ 数据分析完成!")


def cmd_weekly(args):
    """生成周报"""
    from config import ConfigLoader
    from src.services import WeeklyReportService

    # 加载配置
    loader = ConfigLoader(args.config)
    settings = loader.load()

    # 创建服务
    service = WeeklyReportService(settings)

    # 生成周报
    result = service.generate(
        entity_id=args.entity_id,
        workspace_id=args.workspace_id,
        custom_prompt=args.prompt,
        save_to_file=not args.no_save
    )

    print(f"\n✅ 周报生成完成!")
    if 'file_path' in result:
        print(f"文件路径: {result['file_path']}")

    if args.print_report:
        print(f"\n{'-' * 60}")
        print(result['report'])


def cmd_fetch_duplicate(args):
    """获取重复函数数据"""
    from src.core.fetchers import DuplicateFunctionsFetcher

    with DuplicateFunctionsFetcher(config_file=args.config) as fetcher:
        fetcher.run()

    print(f"\n✅ 重复函数数据获取完成!")


def main():
    parser = argparse.ArgumentParser(
        description='Merico 代码质量分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.json',
        help='配置文件路径 (默认: config.json)'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # serve 命令
    serve_parser = subparsers.add_parser('serve', help='启动 Web 服务')
    serve_parser.add_argument('--host', default='0.0.0.0', help='绑定地址')
    serve_parser.add_argument('--port', '-p', type=int, default=8080, help='端口号')
    serve_parser.add_argument('--debug', '-d', action='store_true', help='调试模式')
    serve_parser.set_defaults(func=cmd_serve)

    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='运行代码分析')
    analyze_parser.add_argument(
        '--type', '-t',
        choices=['all', 'uncommented', 'duplicate'],
        default='all',
        help='分析类型'
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # data-analyze 命令
    data_analyze_parser = subparsers.add_parser('data-analyze', help='分析已有数据文件')
    data_analyze_parser.add_argument('--file', '-f', help='数据文件路径')
    data_analyze_parser.add_argument('--export-csv', action='store_true', help='导出CSV')
    data_analyze_parser.add_argument('--export-html', action='store_true', help='导出HTML')
    data_analyze_parser.set_defaults(func=cmd_data_analyze)

    # weekly 命令
    weekly_parser = subparsers.add_parser('weekly', help='生成周报')
    weekly_parser.add_argument('--entity-id', '-e', required=True, help='实体 ID')
    weekly_parser.add_argument('--workspace-id', '-w', required=True, help='工作空间 ID')
    weekly_parser.add_argument('--prompt', '-P', help='自定义提示词')
    weekly_parser.add_argument('--no-save', action='store_true', help='不保存到文件')
    weekly_parser.add_argument('--print-report', action='store_true', help='打印周报内容')
    weekly_parser.set_defaults(func=cmd_weekly)

    # fetch-duplicate 命令
    fetch_dup_parser = subparsers.add_parser('fetch-duplicate', help='获取重复函数数据')
    fetch_dup_parser.set_defaults(func=cmd_fetch_duplicate)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()
