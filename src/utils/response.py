"""
统一 API 响应格式化
"""

from typing import Any, Optional, Dict
from datetime import datetime
from flask import jsonify


class ResponseFormatter:
    """
    API 响应格式化器

    提供统一的成功/失败响应格式
    """

    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """
        成功响应

        Args:
            data: 响应数据
            message: 成功消息
            meta: 元数据（如分页信息）

        Returns:
            (响应体, 状态码) 元组
        """
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat()
        }

        if data is not None:
            response['data'] = data

        if message:
            response['message'] = message

        if meta:
            response['meta'] = meta

        return jsonify(response), 200

    @staticmethod
    def error(
        message: str,
        code: str = 'ERROR',
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """
        错误响应

        Args:
            message: 错误消息
            code: 错误代码
            status_code: HTTP 状态码
            details: 详细错误信息

        Returns:
            (响应体, 状态码) 元组
        """
        response = {
            'success': False,
            'error': {
                'code': code,
                'message': message
            },
            'timestamp': datetime.now().isoformat()
        }

        if details:
            response['error']['details'] = details

        return jsonify(response), status_code

    @staticmethod
    def bad_request(message: str, details: Optional[Dict[str, Any]] = None) -> tuple:
        """400 错误请求"""
        return ResponseFormatter.error(
            message=message,
            code='BAD_REQUEST',
            status_code=400,
            details=details
        )

    @staticmethod
    def not_found(message: str = '资源未找到') -> tuple:
        """404 未找到"""
        return ResponseFormatter.error(
            message=message,
            code='NOT_FOUND',
            status_code=404
        )

    @staticmethod
    def internal_error(message: str = '服务器内部错误') -> tuple:
        """500 内部错误"""
        return ResponseFormatter.error(
            message=message,
            code='INTERNAL_ERROR',
            status_code=500
        )

    @staticmethod
    def paginated(
        items: list,
        total: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple:
        """
        分页响应

        Args:
            items: 数据列表
            total: 总数
            page: 当前页码
            page_size: 每页数量

        Returns:
            (响应体, 状态码) 元组
        """
        total_pages = (total + page_size - 1) // page_size

        return ResponseFormatter.success(
            data=items,
            meta={
                'pagination': {
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
        )
