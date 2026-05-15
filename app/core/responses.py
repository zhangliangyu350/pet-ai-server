from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = "") -> Dict[str, Any]:
    return {
        "success": True,
        "data": {} if data is None else data,
        "message": message,
    }


def error_response(
    code: str,
    message: str,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    return {
        "success": False,
        "data": data,
        "message": message,
        "code": code,
    }

