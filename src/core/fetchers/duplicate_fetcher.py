"""
Merico 重复函数获取器

获取项目中的重复函数列表
使用新架构的公共模块
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.utils import HttpClient, HttpClientConfig, LoggerFactory


class DuplicateFunctionsFetcher:
    """重复函数列表获取器"""

    def __init__(self, settings=None, config_file: str = "config.json"):
        """
        初始化获取器

        Args:
            settings: Settings 配置对象（新架构）
            config_file: 配置文件路径（兼容旧架构）
        """
        self.logger = LoggerFactory.get_logger(__name__)
        self.results = []

        if settings:
            self._init_from_settings(settings)
        else:
            self._init_from_config_file(config_file)

        # 初始化 HTTP 客户端
        self.http_client = HttpClient(self.request_config)
        self.http_client.set_auth_token(self.token)

    def _init_from_settings(self, settings):
        """从 Settings 对象初始化"""
        self.api_url = getattr(settings.merico, 'duplicate_url', '')
        self.token = settings.merico.token
        self.repo_ids_file = settings.merico.repo_ids_file
        self.output_dir = settings.output.output_dir
        self.request_config = HttpClientConfig(
            timeout=settings.request.timeout,
            retry_times=settings.request.retry_times,
            retry_delay=settings.request.retry_delay
        )
        self.batch_delay = settings.request.batch_delay
        self.output_settings = {
            'pretty_print': settings.output.pretty_print
        }

    def _init_from_config_file(self, config_file: str):
        """从配置文件初始化"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.api_url = config.get("duplicate_url", "")
        self.token = config.get("token", "")
        self.repo_ids_file = config.get("repo_ids_file", "repoIds_simple.json")
        self.output_dir = Path("output")

        request_settings = config.get("request_settings", {})
        self.request_config = HttpClientConfig(
            timeout=request_settings.get("timeout", 30),
            retry_times=request_settings.get("retry_times", 3),
            retry_delay=request_settings.get("retry_delay", 2.0)
        )
        self.batch_delay = request_settings.get("batch_delay", 0.5)
        self.output_settings = config.get("output_settings", {})

        self.output_dir.mkdir(exist_ok=True)

    def load_repo_ids(self) -> List[str]:
        """加载项目 ID 列表"""
        with open(self.repo_ids_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def fetch_duplicate_functions(
        self,
        repo_id: str,
        page: int = 1,
        page_size: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个项目的重复函数列表

        Args:
            repo_id: 项目 ID
            page: 页码
            page_size: 每页大小

        Returns:
            API 响应数据，失败则返回 None
        """
        payload = {
            "id": repo_id,
            "page": page,
            "pageSize": page_size,
            "filter": {
                "search": "",
                "emails": ["liuyang2020@staff.hexun.com"]
            },
            "sort": {
                "field": "numFunctions",
                "direction": "desc"
            }
        }

        try:
            response = self.http_client.post(self.api_url, json=payload)
            data = response.json()
            self.logger.info(f"成功获取数据: {data.get('total', 0)}")
            return data

        except Exception as e:
            self.logger.error(f"获取重复函数失败: {e}")
            return None

    def fetch_all_projects(self) -> None:
        """获取所有项目的重复函数列表"""
        repo_ids = self.load_repo_ids()
        total = len(repo_ids)

        self.logger.info(f"开始获取 {total} 个项目的重复函数列表...")
        print("=" * 80)

        for idx, repo_id in enumerate(repo_ids, 1):
            print(f"\n[{idx}/{total}] 处理项目: {repo_id}")

            result = self.fetch_duplicate_functions(repo_id)

            if result:
                self.results.append({
                    "repo_id": repo_id,
                    "data": result,
                    "fetched_at": datetime.now().isoformat()
                })
                print(f"  成功获取数据")
            else:
                self.results.append({
                    "repo_id": repo_id,
                    "data": None,
                    "error": "Failed to fetch",
                    "fetched_at": datetime.now().isoformat()
                })
                print(f"  获取失败")

            # 延迟避免请求过快
            if idx < total:
                time.sleep(self.batch_delay)

        print("\n" + "=" * 80)
        print(f"处理完成! 成功: {sum(1 for r in self.results if r['data'])}/{total}")

    def save_results(self) -> str:
        """保存结果到文件"""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        raw_file = self.output_dir / f"duplicate_functions_{timestamp}.json"

        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(
                self.results,
                f,
                indent=2 if self.output_settings.get("pretty_print", True) else None,
                ensure_ascii=False
            )

        self.logger.info(f"结果已保存到: {raw_file}")

        return timestamp

    def display_summary(self) -> None:
        """显示结果摘要"""
        print("\n" + "=" * 80)
        print("结果摘要")
        print("=" * 80)

        successful = [r for r in self.results if r['data']]
        failed = [r for r in self.results if not r['data']]

        print(f"总项目数: {len(self.results)}")
        print(f"成功: {len(successful)}")
        print(f"失败: {len(failed)}")

        if successful:
            print("\n" + "-" * 80)
            print("成功获取数据的项目示例（前 3 个）:")
            for result in successful[:3]:
                data = result['data']
                print(f"\n项目 ID: {result['repo_id']}")

                if isinstance(data, dict):
                    if 'total' in data:
                        print(f"  总数: {data['total']}")
                    if 'data' in data and isinstance(data['data'], list):
                        print(f"  返回记录数: {len(data['data'])}")
                    print(f"  数据字段: {', '.join(data.keys())}")

        if failed:
            print("\n" + "-" * 80)
            print("失败的项目 ID:")
            for result in failed[:10]:
                print(f"  - {result['repo_id']}")
            if len(failed) > 10:
                print(f"  ... 还有 {len(failed) - 10} 个")

    def run(self) -> Dict[str, Any]:
        """执行完整流程"""
        self.logger.info("Merico 重复函数列表获取工具")
        print("=" * 80)

        # 获取数据
        self.fetch_all_projects()

        # 保存结果
        timestamp = self.save_results()

        # 显示摘要
        self.display_summary()

        # 生成增强的展示报告
        print("\n" + "=" * 80)
        print("正在生成增强的展示报告...")
        print("=" * 80)

        try:
            from src.core.analyzers import DuplicateFunctionsDisplay

            output_file = self.output_dir / f"duplicate_functions_{timestamp}.json"
            display = DuplicateFunctionsDisplay(str(output_file))

            # 生成HTML报告
            html_file = display.generate_html_report()

            # 导出CSV
            csv_file = display.export_csv()

            print("\n✨ 增强报告生成完成!")
            print(f"   HTML报告: {html_file}")
            print(f"   CSV导出:  {csv_file}")

        except ImportError as e:
            self.logger.warning(f"未找到展示模块: {e}")
        except Exception as e:
            self.logger.warning(f"生成增强报告时出错: {e}")

        return {
            'total': len(self.results),
            'successful': sum(1 for r in self.results if r['data']),
            'failed': sum(1 for r in self.results if not r['data']),
            'timestamp': timestamp
        }

    def close(self):
        """关闭资源"""
        self.http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
