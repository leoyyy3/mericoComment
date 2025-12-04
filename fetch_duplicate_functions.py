"""
获取 Merico 项目重复函数列表
根据 require.md 中的需求实现
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
import logging


class DuplicateFunctionsFetcher:
    """重复函数列表获取器"""

    def __init__(self, config_file="config.json"):
        """初始化配置"""
        self.load_config(config_file)
        self.results = []
        self.log_dir = Path("log")
        self._setup_logging()

    def _setup_logging(self):
        """配置日志系统"""
        log_file = self.log_dir / f'duplicate_functions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_file):
        """加载配置文件"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.api_url = config.get("duplicate_url")
        self.token = config.get("token")
        self.repo_ids_file = config.get("repo_ids_file")
        self.request_settings = config.get("request_settings", {})
        self.output_settings = config.get("output_settings", {})

    def load_repo_ids(self):
        """加载项目 ID 列表"""
        with open(self.repo_ids_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def fetch_duplicate_functions(self, repo_id, page=1, page_size=100):
        """
        获取单个项目的重复函数列表

        Args:
            repo_id: 项目 ID
            page: 页码（默认为 1）
            page_size: 每页大小（默认为 100）

        Returns:
            dict: API 响应数据，如果失败则返回 None
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # 按照正确的格式构建请求体
        # params 数组第一个元素是 repo_id，第二个元素是参数对象
        payload = {
            "id": repo_id,
            "page": 1,
            "pageSize": 100,
            "filter": {
                "search": "",
                "emails": [
                    "liuyang2020@staff.hexun.com"
                ]
            },
            "sort": {
                "field": "numFunctions",
                "direction": "desc"
            }
        }

        retry_times = self.request_settings.get("retry_times", 3)
        retry_delay = self.request_settings.get("retry_delay", 2)
        timeout = self.request_settings.get("timeout", 30)

        for attempt in range(retry_times):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )

                response.raise_for_status()
                self.logger.info(f"  成功获取数据: {response.json()['total']}")
                return response.json()

            except requests.exceptions.HTTPError as e:
                print(f"  HTTP 错误 (尝试 {attempt + 1}/{retry_times}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(retry_delay)
                else:
                    print(f"  失败: {response.text if response else 'No response'}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"  请求错误 (尝试 {attempt + 1}/{retry_times}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(retry_delay)
                else:
                    return None

            except Exception as e:
                print(f"  未知错误: {e}")
                return None

        return None

    def fetch_all_projects(self):
        """获取所有项目的重复函数列表"""
        repo_ids = self.load_repo_ids()
        total = len(repo_ids)

        print(f"开始获取 {total} 个项目的重复函数列表...")
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
                print(f"  获取失败")
                self.results.append({
                    "repo_id": repo_id,
                    "data": None,
                    "error": "Failed to fetch",
                    "fetched_at": datetime.now().isoformat()
                })

            # 延迟避免请求过快
            if idx < total:
                delay = self.request_settings.get("batch_delay", 0.5)
                time.sleep(delay)

        print("\n" + "=" * 80)
        print(f"处理完成! 成功: {sum(1 for r in self.results if r['data'])}/{total}")

    def save_results(self):
        """保存结果到文件"""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.output_settings.get("save_raw", True):
            raw_file = output_dir / f"duplicate_functions_{timestamp}.json"

            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.results,
                    f,
                    indent=2 if self.output_settings.get("pretty_print", True) else None,
                    ensure_ascii=False
                )

            print(f"\n原始结果已保存到: {raw_file}")

        return timestamp

    def display_summary(self):
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

                # 显示数据结构信息
                if isinstance(data, dict):
                    if 'total' in data:
                        print(f"  总数: {data['total']}")
                    if 'data' in data and isinstance(data['data'], list):
                        print(f"  返回记录数: {len(data['data'])}")
                    if 'page' in data:
                        print(f"  页码: {data['page']}")
                    print(f"  数据字段: {', '.join(data.keys())}")

        if failed:
            print("\n" + "-" * 80)
            print("失败的项目 ID:")
            for result in failed[:10]:
                print(f"  - {result['repo_id']}")
            if len(failed) > 10:
                print(f"  ... 还有 {len(failed) - 10} 个")

    def run(self):
        """执行完整流程"""
        print("Merico 重复函数列表获取工具")
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
            from display_duplicate_functions import DuplicateFunctionsDisplay
            
            # 使用刚保存的文件
            output_file = Path("output") / f"duplicate_functions_{timestamp}.json"
            display = DuplicateFunctionsDisplay(str(output_file))
            
            # 生成HTML报告
            html_file = display.generate_html_report()
            
            # 导出CSV
            csv_file = display.export_csv()
            
            print("\n✨ 增强报告生成完成!")
            print(f"   HTML报告: {html_file}")
            print(f"   CSV导出:  {csv_file}")
            
        except ImportError:
            print("⚠️  未找到 display_duplicate_functions 模块，跳过增强报告生成")
        except Exception as e:
            print(f"⚠️  生成增强报告时出错: {e}")



def main():
    """主函数"""
    fetcher = DuplicateFunctionsFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
