from enum import Enum
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    auth_required = "AUTH_REQUIRED"
    login_failed = "LOGIN_FAILED"
    image_required = "IMAGE_REQUIRED"
    image_type_invalid = "IMAGE_TYPE_INVALID"
    image_size_exceeded = "IMAGE_SIZE_EXCEEDED"
    upload_failed = "UPLOAD_FAILED"
    analysis_busy = "ANALYSIS_BUSY"
    analysis_failed = "ANALYSIS_FAILED"
    analysis_limit_exceeded = "ANALYSIS_LIMIT_EXCEEDED"
    analysis_too_frequent = "ANALYSIS_TOO_FREQUENT"
    record_not_found = "RECORD_NOT_FOUND"
    validation_error = "VALIDATION_ERROR"
    server_error = "SERVER_ERROR"


DEFAULT_MESSAGES = {
    ErrorCode.auth_required: "请先登录后继续",
    ErrorCode.login_failed: "登录失败，请重试",
    ErrorCode.image_required: "请先上传便便照片",
    ErrorCode.image_type_invalid: "仅支持 JPG、PNG 图片",
    ErrorCode.image_size_exceeded: "图片不能超过 10MB",
    ErrorCode.upload_failed: "图片上传失败，请重试",
    ErrorCode.analysis_busy: "当前分析人数较多，请稍后再试",
    ErrorCode.analysis_failed: "分析失败，请稍后重试",
    ErrorCode.analysis_limit_exceeded: "今日分析次数已用完",
    ErrorCode.analysis_too_frequent: "请 10 秒后再试",
    ErrorCode.record_not_found: "记录不存在或已删除",
    ErrorCode.validation_error: "请检查输入内容",
    ErrorCode.server_error: "服务异常，请稍后再试",
}


class BusinessError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        status_code: int = 400,
    ) -> None:
        """Create a business exception with contract error code and HTTP status."""
        self.code = code
        self.message = message or DEFAULT_MESSAGES[code]
        self.status_code = status_code
        super().__init__(self.message)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers that preserve the public API contract."""
    @app.exception_handler(BusinessError)
    async def handle_business_error(
        _request: Request,
        exc: BusinessError,
    ) -> JSONResponse:
        """Convert known business errors into structured JSON responses."""
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=exc.code.value, message=exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        """Convert FastAPI validation errors into the shared validation error code."""
        return JSONResponse(
            status_code=422,
            content=error_response(
                code=ErrorCode.validation_error.value,
                message=DEFAULT_MESSAGES[ErrorCode.validation_error],
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
        """Hide unexpected internal errors behind a generic server error response."""
        logger.exception("Unhandled error while processing %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=ErrorCode.server_error.value,
                message=DEFAULT_MESSAGES[ErrorCode.server_error],
            ),
        )
