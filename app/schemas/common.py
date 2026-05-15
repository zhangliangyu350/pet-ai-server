from typing import Any, Optional

from pydantic import BaseModel


class ApiSuccessResponse(BaseModel):
    success: bool = True
    data: Any
    message: str = ""


class ApiErrorResponse(BaseModel):
    success: bool = False
    data: Optional[Any] = None
    message: str
    code: str

