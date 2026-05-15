from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WechatLoginRequest(BaseModel):
    code: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    nickname: str
    avatar_url: str = Field(serialization_alias="avatarUrl")
    created_at: datetime = Field(serialization_alias="createdAt")


class LoginResult(BaseModel):
    token: str
    user: UserResponse


class WechatSession(BaseModel):
    openid: str
    session_key: str = ""
    unionid: str = ""


class AuthSession(BaseModel):
    user_id: str
    openid: str

