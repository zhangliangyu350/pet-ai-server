import json

import pytest

from app.services.ai_service import DoubaoAIClient
from tests.image_fixtures import PNG_1X1


class MockResponse:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "score": 82,
                                "riskLevel": "low",
                                "summary": "状态较稳定",
                                "observationAdvice": ["继续观察"],
                                "dietAdvice": "保持饮水",
                                "needVet": False,
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }


class MockAsyncClient:
    captured_payload = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        pass

    async def post(self, url: str, json: dict, headers: dict):
        self.__class__.captured_payload = json
        return MockResponse()


@pytest.mark.anyio
async def test_doubao_client_sends_base64_image_content(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
    client = DoubaoAIClient(
        api_key="api_key",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        max_attempts=1,
    )

    await client.analyze_poop_image(
        image_content=PNG_1X1,
        image_type="png",
        pet_type="dog",
        pet_name="狗狗",
    )

    assert MockAsyncClient.captured_payload["model"] == "doubao-vision-pro"
    user_message = MockAsyncClient.captured_payload["messages"][1]
    assert user_message["content"][0]["type"] == "text"
    image_url = user_message["content"][1]["image_url"]["url"]
    assert user_message["content"][1]["type"] == "image_url"
    assert image_url.startswith("data:image/png;base64,")
