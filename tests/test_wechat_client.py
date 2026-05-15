import httpx
import pytest

from app.core.exceptions import BusinessError, ErrorCode
from app.services.wechat_client import WechatClient


class MockResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "failed",
                request=httpx.Request("GET", "https://example.com"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self.payload


class MockAsyncClient:
    payload = {}
    status_code = 200

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        pass

    async def get(self, url: str, params: dict):
        return MockResponse(self.payload, self.status_code)


@pytest.mark.anyio
async def test_wechat_client_returns_session(monkeypatch):
    MockAsyncClient.payload = {"openid": "openid_001", "session_key": "session_key"}
    MockAsyncClient.status_code = 200
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    session = await WechatClient(app_id="appid", app_secret="secret").code_to_session("code")

    assert session.openid == "openid_001"
    assert session.session_key == "session_key"


@pytest.mark.anyio
async def test_wechat_client_maps_wechat_error(monkeypatch):
    MockAsyncClient.payload = {"errcode": 40029, "errmsg": "invalid code"}
    MockAsyncClient.status_code = 200
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    with pytest.raises(BusinessError) as exc_info:
        await WechatClient(app_id="appid", app_secret="secret").code_to_session("bad_code")

    assert exc_info.value.code == ErrorCode.login_failed


@pytest.mark.anyio
async def test_wechat_client_requires_credentials():
    with pytest.raises(BusinessError) as exc_info:
        await WechatClient(app_id="", app_secret="").code_to_session("code")

    assert exc_info.value.code == ErrorCode.login_failed

