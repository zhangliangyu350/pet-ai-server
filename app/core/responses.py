from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = "") -> Dict[str, Any]:
    """Wrap successful API data in the frontend response contract."""
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
    """Wrap API errors in the frontend response contract."""
    return {
        "success": False,
        "data": data,
        "message": message,
        "code": code,
    }
