"""
周报生成器

根据 entity_id 和 workspace_id 从 TAPD 获取提交记录，
使用智谱 AI 生成周报。

使用新架构的公共模块
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from zhipuai import ZhipuAI

from src.utils import HttpClient, HttpClientConfig, LoggerFactory


class TAPDClient:
    """TAPD API 客户端，用于获取提交记录"""

    def __init__(self, config: Dict[str, Any] = None, settings=None):
        """
        初始化 TAPD 客户端

        Args:
            config: TAPD 配置字典，包含 base_url 和 cookies
            settings: Settings 配置对象（新架构）
        """
        self.logger = LoggerFactory.get_logger(__name__)

        if settings:
            self._init_from_settings(settings)
        elif config:
            self._init_from_config(config)
        else:
            raise ValueError("需要提供 config 或 settings 参数")

        # 初始化 HTTP 客户端
        http_config = HttpClientConfig(
            timeout=self._timeout,
            retry_times=self._retry_times,
            retry_delay=self._retry_delay,
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
        )
        self.http_client = HttpClient(http_config)

        # 设置 cookies
        self.http_client.set_cookies(self.cookies)

    def _init_from_settings(self, settings):
        """从 Settings 对象初始化"""
        self.base_url = settings.tapd.base_url
        self.cookies = settings.tapd.cookies or {}
        self._timeout = settings.request.timeout
        self._retry_times = settings.request.retry_times
        self._retry_delay = settings.request.retry_delay

    def _init_from_config(self, config: Dict[str, Any]):
        """从配置字典初始化"""
        self.base_url = config.get('base_url', 'https://www.tapd.cn/api/devops/source_code')
        self.cookies = config.get('cookies', {})
        self._timeout = 30
        self._retry_times = 3
        self._retry_delay = 2.0

    def fetch_commits(
        self,
        entity_id: str,
        workspace_id: str,
        entity_type: str = 'story',
        related_id: str = '-1',
        page: int = 1,
        per_page: int = 100,
        scm_type: str = 'gitlab'
    ) -> Dict[str, Any]:
        """
        获取指定实体的提交记录

        Args:
            entity_id: 实体 ID
            workspace_id: 工作空间 ID
            entity_type: 实体类型，默认 'story'
            related_id: 关联 ID，默认 '-1'
            page: 页码，默认 1
            per_page: 每页数量，默认 100
            scm_type: SCM 类型，默认 'gitlab'

        Returns:
            API 响应数据
        """
        url = f"{self.base_url}/get_related_commits"

        params = {
            'workspace_id': workspace_id,
            'entity_id': entity_id,
            'entity_type': entity_type,
            'related_id': related_id,
            'page': page,
            'per_page': per_page,
            'scm_type': scm_type
        }

        self.logger.info(f"Fetching commits: entity_id={entity_id}, page={page}")
        response = self.http_client.get(url, params=params)
        data = response.json()

        # 检查响应状态
        if data.get('meta', {}).get('code') != '0':
            error_msg = data.get('meta', {}).get('message', 'Unknown error')
            self.logger.error(f"TAPD API error: {error_msg}")
            raise Exception(f"TAPD API error: {error_msg}")

        self.logger.info(f"Fetched {len(data.get('data', {}).get('commits', []))} commits")
        return data

    def fetch_all_commits(
        self,
        entity_id: str,
        workspace_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        获取所有提交记录（处理分页）

        Args:
            entity_id: 实体 ID
            workspace_id: 工作空间 ID
            **kwargs: 其他参数

        Returns:
            所有提交记录列表
        """
        all_commits = []
        page = 1
        per_page = kwargs.get('per_page', 100)

        while True:
            response = self.fetch_commits(
                entity_id=entity_id,
                workspace_id=workspace_id,
                page=page,
                per_page=per_page,
                **{k: v for k, v in kwargs.items() if k != 'per_page'}
            )

            commits = response.get('data', {}).get('commits', [])
            if not commits:
                break

            all_commits.extend(commits)

            # 检查是否还有更多数据
            total_count = int(response.get('data', {}).get('total_count', 0))
            if len(all_commits) >= total_count:
                break

            page += 1

        self.logger.info(f"Total commits fetched: {len(all_commits)}")
        return all_commits

    def extract_commit_info(self, commits: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        从提交记录中提取 message 和 user_name

        Args:
            commits: 提交记录列表

        Returns:
            提取的信息列表
        """
        extracted = []
        for commit in commits:
            extracted.append({
                'message': commit.get('message', ''),
                'user_name': commit.get('user_name', ''),
                'commit_time': commit.get('commit_time', ''),
                'commit_id': commit.get('commit_id', '')
            })

        self.logger.info(f"Extracted info from {len(extracted)} commits")
        return extracted

    def close(self):
        """关闭资源"""
        self.http_client.close()


class ZhipuAIClient:
    """智谱 AI 客户端，用于生成周报"""

    def __init__(self, config: Dict[str, Any] = None, settings=None):
        """
        初始化智谱 AI 客户端

        Args:
            config: 智谱 AI 配置字典，包含 api_key 和 model
            settings: Settings 配置对象（新架构）
        """
        self.logger = LoggerFactory.get_logger(__name__)

        if settings:
            self.api_key = settings.zhipu_ai.api_key
            self.model = settings.zhipu_ai.model
        elif config:
            self.api_key = config.get('api_key')
            self.model = config.get('model', 'glm-4.5-flash')
        else:
            raise ValueError("需要提供 config 或 settings 参数")

        if not self.api_key:
            raise ValueError("Zhipu AI API key is required")

        self.client = ZhipuAI(api_key=self.api_key)
        self.logger.info(f"Initialized Zhipu AI client with model: {self.model}")

    def generate_weekly_report(
        self,
        commits_data: List[Dict[str, str]],
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        根据提交数据生成周报

        Args:
            commits_data: 提交信息列表
            custom_prompt: 自定义提示词（可选）

        Returns:
            生成的周报内容
        """
        if not commits_data:
            self.logger.warning("No commits data provided")
            return "没有提交记录可供分析。"

        # 构建提示词
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._build_default_prompt(commits_data)

        self.logger.info(f"Generating weekly report with {len(commits_data)} commits")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的技术周报生成助手，擅长分析代码提交记录并生成清晰、专业的周报。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            top_p=0.9,
        )

        report = response.choices[0].message.content
        self.logger.info("Successfully generated weekly report")
        return report

    def _build_default_prompt(self, commits_data: List[Dict[str, str]]) -> str:
        """构建默认的提示词"""
        # 按用户分组统计
        user_commits = {}
        for commit in commits_data:
            user_name = commit['user_name']
            if user_name not in user_commits:
                user_commits[user_name] = []
            user_commits[user_name].append(commit)

        # 构建提交记录文本
        commits_text = "## 提交记录详情\n\n"
        for user_name, commits in user_commits.items():
            commits_text += f"### {user_name} ({len(commits)} 次提交)\n\n"
            for commit in commits:
                commits_text += f"- **时间**: {commit.get('commit_time', 'N/A')}\n"
                commits_text += f"  **消息**: {commit['message'].strip()}\n\n"

        prompt = f"""请根据以下代码提交记录生成一份专业的技术周报。

{commits_text}

请按以下格式生成周报：

# 本周工作总结

## 一、整体概述
简要概述本周的主要工作内容和成果。

## 二、详细工作内容
按功能模块或任务分类，详细说明：
# 1. 完成的功能或修复的问题
# 2. 技术要点和实现方案
# 3. 遇到的挑战和解决方法

请确保：
- 语言专业、简洁
- 突出重点工作
- 合理归纳和分类
- 避免简单罗列提交信息
"""
        return prompt


class WeeklyReportGenerator:
    """周报生成器主类"""

    def __init__(self, settings=None, config_path: str = None):
        """
        初始化周报生成器

        Args:
            settings: Settings 配置对象（新架构优先）
            config_path: 配置文件路径（兼容旧架构）
        """
        self.logger = LoggerFactory.get_logger(__name__)

        if settings:
            self._init_from_settings(settings)
        elif config_path:
            self._init_from_config_file(config_path)
        else:
            # 默认使用 config.json
            self._init_from_config_file('config.json')

        self.logger.info("WeeklyReportGenerator initialized successfully")

    def _init_from_settings(self, settings):
        """从 Settings 对象初始化"""
        self.tapd_client = TAPDClient(settings=settings)
        self.ai_client = ZhipuAIClient(settings=settings)

    def _init_from_config_file(self, config_path: str):
        """从配置文件初始化"""
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.tapd_client = TAPDClient(config=config.get('tapd', {}))
        self.ai_client = ZhipuAIClient(config=config.get('zhipu_ai', {}))

    def generate_report(
        self,
        entity_id: str,
        workspace_id: str,
        output_file: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        生成周报

        Args:
            entity_id: TAPD 实体 ID
            workspace_id: TAPD 工作空间 ID
            output_file: 输出文件路径（可选）
            custom_prompt: 自定义提示词（可选）

        Returns:
            生成的周报内容
        """
        self.logger.info(f"Starting report generation: entity_id={entity_id}")

        # 1. 获取提交记录
        commits = self.tapd_client.fetch_all_commits(entity_id, workspace_id)

        if not commits:
            self.logger.warning("No commits found")
            return "未找到提交记录。"

        # 2. 提取关键信息
        commits_info = self.tapd_client.extract_commit_info(commits)

        # 3. 生成周报
        report = self.ai_client.generate_weekly_report(commits_info, custom_prompt)

        # 4. 保存到文件（如果指定）
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"Report saved to {output_file}")

        return report

    def close(self):
        """关闭资源"""
        self.tapd_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
