"""
统一的 HTTP 客户端封装
支持重试、超时、认证等功能
"""

import requests
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
import logging
import time


@dataclass
class HttpClientConfig:
    """HTTP 客户端配置"""
    timeout: int = 30
    retry_times: int = 3
    retry_delay: float = 2.0
    headers: Dict[str, str] = field(default_factory=dict)


class HttpClient:
    """
    统一的 HTTP 客户端

    特性:
    - 自动重试机制
    - 超时控制
    - 统一的错误处理
    - 认证头管理
    """

    def __init__(self, config: Optional[HttpClientConfig] = None):
        """
        初始化 HTTP 客户端

        Args:
            config: 客户端配置
        """
        self.config = config or HttpClientConfig()
        self.logger = logging.getLogger(__name__)
        self._session = requests.Session()

        # 设置默认 headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            **self.config.headers
        })

    def set_auth_token(self, token: str) -> None:
        """设置 Bearer Token 认证"""
        self._session.headers['Authorization'] = f'Bearer {token}'

    def set_cookies(self, cookies: Dict[str, str]) -> None:
        """设置 Cookies"""
        self._session.cookies.update(cookies)

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """
        执行 HTTP 请求，带自动重试

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他请求参数

        Returns:
            响应对象

        Raises:
            requests.exceptions.RequestException: 请求失败
        """
        kwargs.setdefault('timeout', self.config.timeout)

        last_exception = None

        for attempt in range(self.config.retry_times):
            try:
                self.logger.debug(
                    f"请求 {method} {url} (尝试 {attempt + 1}/{self.config.retry_times})"
                )

                response = self._session.request(method, url, **kwargs)
                response.raise_for_status()

                self.logger.debug(f"请求成功: {url}")
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(
                    f"请求失败 (尝试 {attempt + 1}/{self.config.retry_times}): {e}"
                )

                if attempt < self.config.retry_times - 1:
                    time.sleep(self.config.retry_delay)

        self.logger.error(f"请求最终失败: {url}")
        raise last_exception

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """GET 请求"""
        return self._make_request('GET', url, params=params, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Union[Dict, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """POST 请求"""
        return self._make_request('POST', url, data=data, json=json, **kwargs)

    def put(
        self,
        url: str,
        data: Optional[Union[Dict, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """PUT 请求"""
        return self._make_request('PUT', url, data=data, json=json, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE 请求"""
        return self._make_request('DELETE', url, **kwargs)

    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET 请求并返回 JSON"""
        response = self.get(url, **kwargs)
        return response.json()

    def post_json(
        self,
        url: str,
        json_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """POST 请求并返回 JSON"""
        response = self.post(url, json=json_data, **kwargs)
        return response.json()

    def close(self) -> None:
        """关闭会话"""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
