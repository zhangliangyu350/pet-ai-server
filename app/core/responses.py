from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = "") -> Dict[str, Any]:
    """按前端响应契约包装成功 API 数据。"""
    return {
        "success": True,
        "data": data,
        "message": message,
    }


def error_response(
    code: str,
    message: str,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    """按前端响应契约包装 API 错误。"""
    return {
        "success": False,
        "data": data,
        "message": message,
        "code": code,
    }
