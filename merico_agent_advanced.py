"""
Merico Uncommented Functions Agent - 高级配置版本
用于批量请求项目未注释函数列表并进行深度归类分析
支持从配置文件加载参数
"""

import json
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import time
from collections import defaultdict
import argparse
from analyze_data import DataAnalyzer


class MericoUncommentedFunctionsAgent:
    """Merico 项目未注释函数数据采集与分析智能体"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化智能体

        Args:
            config: 配置字典
        """
        self.config = config
        self.token = config["token"]
        self.api_url = config["api_url"]
        self.repo_ids_file = config["repo_ids_file"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # 创建必要的目录
        self.output_dir = Path("output")
        self.log_dir = Path("log")
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        # 配置日志
        self._setup_logging()

        # 数据存储
        self.all_results = []
        self.classified_data = defaultdict(list)
        self.error_projects = []

    def _setup_logging(self):
        """配置日志系统"""
        log_file = self.log_dir / f'merico_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_repo_ids(self) -> List[str]:
        """
        加载项目 ID 列表

        Returns:
            项目 ID 列表
        """
        try:
            with open(self.repo_ids_file, 'r', encoding='utf-8') as f:
                repo_ids = json.load(f)
            self.logger.info(f"成功加载 {len(repo_ids)} 个项目 ID")
            # 截取前10个id
            repo_ids = repo_ids[:10]
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
        """
        构建请求参数

        Args:
            repo_id: 项目 ID
            authors: 作者过滤列表
            page: 页码
            page_size: 每页数量

        Returns:
            请求参数字典
        """
        payload = {
            "params": [
                repo_id,
                {
                    "page": 1,
                    "pageSize": 10,
                    "sortField": "cyclomatic",
                    "sortOrder": "descend",
                    "location": "",
                    "frequentAuthors": [
                        "liuyang2020@staff.hexun.com"
                    ],
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
        """
        请求单个项目的未注释函数列表

        Args:
            repo_id: 项目 ID
            authors: 作者过滤列表

        Returns:
            API 响应数据或 None
        """
        request_settings = self.config.get("request_settings", {})
        retry_times = request_settings.get("retry_times", 3)
        retry_delay = request_settings.get("retry_delay", 2)
        timeout = request_settings.get("timeout", 30)
        page_size = request_settings.get("page_size", 100)

        payload = self.build_request_payload(repo_id, authors, page_size=page_size)

        for attempt in range(retry_times):
            try:
                self.logger.info(f"请求项目 {repo_id} (尝试 {attempt + 1}/{retry_times})")

                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )

                response.raise_for_status()
                data = response.json()

                self.logger.info(f"项目 {repo_id} 请求成功")
                return {
                    "repo_id": repo_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"项目 {repo_id} 请求失败 (尝试 {attempt + 1}/{retry_times}): {e}")

                if attempt < retry_times - 1:
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"项目 {repo_id} 请求最终失败")
                    self.error_projects.append({
                        "repo_id": repo_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    return None

    def classify_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        归类数据

        Args:
            results: 所有项目的响应结果

        Returns:
            归类后的数据
        """
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
            # API 返回结构: {"total": N, "data": [...]}
            if isinstance(data, dict):
                # 从 data.data 或 data 中获取未注释函数列表
                uncommented_functions = []

                # 情况1: data.data (嵌套结构)
                if "data" in data:
                    if isinstance(data["data"], list):
                        uncommented_functions = data["data"]
                    elif isinstance(data["data"], dict) and "list" in data["data"]:
                        uncommented_functions = data["data"]["list"]

                # 情况2: data 本身是列表
                elif "list" in data:
                    uncommented_functions = data["list"]

                classified["summary"]["total_uncommented_functions"] += len(uncommented_functions)

                for func in uncommented_functions:
                    # 添加项目信息
                    func_with_project = {
                        "repo_id": repo_id,
                        **func
                    }
                    classified["all_uncommented_functions"].append(func_with_project)

                    # 按严重程度分类（如果API返回此字段）
                    severity = func.get("severity", "unknown")
                    classified["by_severity"][severity] += 1

                    # 按类型分类（如果API返回此字段）
                    func_type = func.get("type", "unknown")
                    classified["by_type"][func_type] += 1

                    # 按规则分类（如果API返回此字段）
                    rule = func.get("rule", func.get("ruleId", "unknown"))
                    classified["by_rule"][rule] += 1

        # 转换 defaultdict 为普通 dict
        classified["by_severity"] = dict(classified["by_severity"])
        classified["by_type"] = dict(classified["by_type"])
        classified["by_rule"] = dict(classified["by_rule"])

        return classified

    def save_results(
        self,
        data: Any,
        filename: str,
        pretty: bool = True
    ):
        """
        保存结果到文件

        Args:
            data: 要保存的数据
            filename: 文件名
            pretty: 是否格式化输出
        """
        try:
            # 将文件保存到 output 目录
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
        """
        生成可读性报告

        Args:
            classified: 归类后的数据

        Returns:
            报告文本
        """
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

        report.append("## 按规则分类 (Top 10)")
        for rule, count in sorted(classified["by_rule"].items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"- {rule}: {count}")
        report.append("")

        if classified["errors"]:
            report.append("## 失败的项目")
            for error in classified["errors"]:
                report.append(f"- {error['repo_id']}: {error['error']}")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def run(self):
        """
        运行智能体，批量处理所有项目
        """
        self.logger.info("=" * 80)
        self.logger.info("Merico 未注释函数分析智能体开始运行")
        self.logger.info("=" * 80)

        # 加载项目 ID
        repo_ids = self.load_repo_ids()

        # 获取配置
        authors = self.config.get("authors", [])
        request_settings = self.config.get("request_settings", {})
        output_settings = self.config.get("output_settings", {})
        batch_delay = request_settings.get("batch_delay", 0.5)

        # 批量请求
        self.logger.info(f"开始批量请求 {len(repo_ids)} 个项目...")
        for i, repo_id in enumerate(repo_ids, 1):
            self.logger.info(f"进度: {i}/{len(repo_ids)}")

            result = self.fetch_uncommented_functions(repo_id, authors if authors else None)
            if result:
                self.all_results.append(result)

            # 添加延���避免请求过快
            if i < len(repo_ids):
                time.sleep(batch_delay)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存原始数据
        if output_settings.get("save_raw", True):
            self.save_results(
                self.all_results,
                f"raw_results_{timestamp}.json",
                pretty=output_settings.get("pretty_print", True)
            )

        # 归类数据
        self.logger.info("开始归类数据...")
        classified = self.classify_data(self.all_results)

        # 保存归类数据
        if output_settings.get("save_classified", True):
            self.save_results(
                classified,
                f"classified_results_{timestamp}.json",
                pretty=output_settings.get("pretty_print", True)
            )

        # 使用归类后的数据创建分析器并生成 HTML 报告
        analyzer = DataAnalyzer(data=classified)
        analyzer.export_html()

        # 生成并保存文本报告
        report = self.generate_report(classified)
        report_path = self.output_dir / f"uncommment_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self.logger.info(f"报告已保存到: {report_path}")

        # 打印报告
        print("\n" + report)

        return classified


def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Merico 未注释函数分析智能体')
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='配置文件路径 (默认: config.json)'
    )
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    # 创建智能体
    agent = MericoUncommentedFunctionsAgent(config)

    # 运行
    agent.run()


if __name__ == "__main__":
    main()
