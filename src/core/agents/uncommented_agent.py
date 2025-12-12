"""
Merico 未注释函数智能体

用于批量请求项目未注释函数列表并进行深度归类分析
使用新架构的公共模块
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from src.utils import HttpClient, HttpClientConfig, LoggerFactory, retry


class UncommentedFunctionsAgent:
    """Merico 项目未注释函数数据采集与分析智能体"""

    def __init__(self, settings=None, config: Dict[str, Any] = None):
        """
        初始化智能体

        Args:
            settings: Settings 配置对象（新架构）
            config: 配置字典（兼容旧架构）
        """
        self.settings = settings
        self.config = config or {}
        self.logger = LoggerFactory.get_logger(__name__)

        # 从 settings 或 config 获取配置
        if settings:
            self.token = settings.merico.token
            self.api_url = settings.merico.api_url
            self.repo_ids_file = settings.merico.repo_ids_file
            self.output_dir = settings.output.output_dir
            self.request_config = HttpClientConfig(
                timeout=settings.request.timeout,
                retry_times=settings.request.retry_times,
                retry_delay=settings.request.retry_delay
            )
            self.batch_delay = settings.request.batch_delay
            self.output_settings = {
                'save_classified': settings.output.save_classified,
                'pretty_print': settings.output.pretty_print
            }
        else:
            self.token = config.get("token", "")
            self.api_url = config.get("api_url", "")
            self.repo_ids_file = config.get("repo_ids_file", "repoIds_simple.json")
            self.output_dir = Path(config.get("output_settings", {}).get("output_dir", "output"))
            request_settings = config.get("request_settings", {})
            self.request_config = HttpClientConfig(
                timeout=request_settings.get("timeout", 30),
                retry_times=request_settings.get("retry_times", 3),
                retry_delay=request_settings.get("retry_delay", 2.0)
            )
            self.batch_delay = request_settings.get("batch_delay", 0.5)
            self.output_settings = config.get("output_settings", {})

        # 确保输出目录存在
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 初始化 HTTP 客户端
        self.http_client = HttpClient(self.request_config)
        self.http_client.set_auth_token(self.token)

        # 数据存储
        self.all_results = []
        self.error_projects = []

    def load_repo_ids(self) -> List[str]:
        """加载项目 ID 列表"""
        try:
            with open(self.repo_ids_file, 'r', encoding='utf-8') as f:
                repo_ids = json.load(f)
            self.logger.info(f"成功加载 {len(repo_ids)} 个项目 ID")
            return repo_ids
        except Exception as e:
            self.logger.error(f"加载项目 ID 文件失败: {e}")
            raise

    def build_request_payload(
        self,
        repo_id: str,
        authors: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """构建请求参数"""
        payload = {
            "params": [
                repo_id,
                {
                    "page": page,
                    "pageSize": page_size,
                    "sortField": "cyclomatic",
                    "sortOrder": "descend",
                    "location": "",
                    "frequentAuthors": authors or ["liuyang2020@staff.hexun.com"],
                    "cyclomatic": {
                        "min": 0,
                        "max": None
                    },
                    "isDocCovered": False
                }
            ]
        }
        return payload

    def fetch_uncommented_functions(
        self,
        repo_id: str,
        authors: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """请求单个项目的未注释函数列表"""
        payload = self.build_request_payload(repo_id, authors)

        try:
            self.logger.info(f"请求项目 {repo_id}")
            response = self.http_client.post(self.api_url, json=payload)
            data = response.json()

            self.logger.info(f"项目 {repo_id} 请求成功")
            return {
                "repo_id": repo_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"项目 {repo_id} 请求失败: {e}")
            self.error_projects.append({
                "repo_id": repo_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None

    def classify_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """归类数据"""
        classified = {
            "summary": {
                "total_projects": len(results) + len(self.error_projects),
                "successful_projects": 0,
                "failed_projects": len(self.error_projects),
                "total_uncommented_functions": 0
            },
            "by_project": {},
            "by_severity": defaultdict(int),
            "by_type": defaultdict(int),
            "by_rule": defaultdict(int),
            "all_uncommented_functions": [],
            "errors": self.error_projects
        }

        for result in results:
            if not result:
                continue

            repo_id = result["repo_id"]
            data = result["data"]

            classified["summary"]["successful_projects"] += 1
            classified["by_project"][repo_id] = {
                "data": data,
                "timestamp": result["timestamp"]
            }

            # 提取和归类未注释函数数据
            if isinstance(data, dict):
                uncommented_functions = []

                if "data" in data:
                    if isinstance(data["data"], list):
                        uncommented_functions = data["data"]
                    elif isinstance(data["data"], dict) and "list" in data["data"]:
                        uncommented_functions = data["data"]["list"]
                elif "list" in data:
                    uncommented_functions = data["list"]

                classified["summary"]["total_uncommented_functions"] += len(uncommented_functions)

                for func in uncommented_functions:
                    func_with_project = {"repo_id": repo_id, **func}
                    classified["all_uncommented_functions"].append(func_with_project)

                    severity = func.get("severity", "unknown")
                    classified["by_severity"][severity] += 1

                    func_type = func.get("type", "unknown")
                    classified["by_type"][func_type] += 1

                    rule = func.get("rule", func.get("ruleId", "unknown"))
                    classified["by_rule"][rule] += 1

        # 转换 defaultdict 为普通 dict
        classified["by_severity"] = dict(classified["by_severity"])
        classified["by_type"] = dict(classified["by_type"])
        classified["by_rule"] = dict(classified["by_rule"])

        return classified

    def save_results(self, data: Any, filename: str, pretty: bool = True):
        """保存结果到文件"""
        try:
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(data, f, ensure_ascii=False)
            self.logger.info(f"结果已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")

    def generate_report(self, classified: Dict[str, Any]) -> str:
        """生成可读性报告"""
        report = []
        report.append("=" * 80)
        report.append("Merico 项目未注释函数分析报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        summary = classified["summary"]
        report.append("## 总体统计")
        report.append(f"- 总项目数: {summary['total_projects']}")
        report.append(f"- 成功项目数: {summary['successful_projects']}")
        report.append(f"- 失败项目数: {summary['failed_projects']}")
        report.append(f"- 总未注释函数数: {summary['total_uncommented_functions']}")
        report.append("")

        report.append("## 按严重程度分类")
        for severity, count in sorted(classified["by_severity"].items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {severity}: {count}")
        report.append("")

        report.append("## 按类型分类 (Top 10)")
        for issue_type, count in sorted(classified["by_type"].items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"- {issue_type}: {count}")
        report.append("")

        if classified["errors"]:
            report.append("## 失败的项目")
            for error in classified["errors"]:
                report.append(f"- {error['repo_id']}: {error['error']}")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)

    def run(self) -> Dict[str, Any]:
        """运行智能体，批量处理所有项目"""
        import time

        self.logger.info("=" * 80)
        self.logger.info("Merico 未注释函数分析智能体开始运行")
        self.logger.info("=" * 80)

        # 加载项目 ID
        repo_ids = self.load_repo_ids()

        # 获取配置
        authors = self.config.get("authors", [])

        # 批量请求
        self.logger.info(f"开始批量请求 {len(repo_ids)} 个项目...")
        for i, repo_id in enumerate(repo_ids, 1):
            self.logger.info(f"进度: {i}/{len(repo_ids)}")

            result = self.fetch_uncommented_functions(repo_id, authors if authors else None)
            if result:
                self.all_results.append(result)

            # 添加延迟避免请求过快
            if i < len(repo_ids):
                time.sleep(self.batch_delay)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 归类数据
        self.logger.info("开始归类数据...")
        classified = self.classify_data(self.all_results)

        # 保存归类数据
        if self.output_settings.get("save_classified", True):
            self.save_results(
                classified,
                f"classified_results_{timestamp}.json",
                pretty=self.output_settings.get("pretty_print", True)
            )

        # 生成 HTML 报告
        try:
            from src.core.analyzers import DataAnalyzer
            analyzer = DataAnalyzer(data=classified)
            analyzer.export_html()
        except Exception as e:
            self.logger.warning(f"生成 HTML 报告失败: {e}")

        # 生成并保存文本报告
        report = self.generate_report(classified)
        report_path = self.output_dir / "uncommment_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self.logger.info(f"报告已保存到: {report_path}")

        print("\n" + report)

        return classified

    def close(self):
        """关闭资源"""
        self.http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
