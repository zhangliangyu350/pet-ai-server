import json

import pytest

from app.services.ai_service import DeepSeekAIClient


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
async def test_deepseek_client_sends_image_url_content(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
    client = DeepSeekAIClient(
        api_key="api_key",
        base_url="https://api.deepseek.com",
        max_attempts=1,
    )

    await client.analyze_poop_image(
        image_url="https://cdn.example.com/pet-ai-images/images/image_001.png",
        pet_type="dog",
        pet_name="狗狗",
    )

    user_message = MockAsyncClient.captured_payload["messages"][1]
    assert user_message["content"][0]["type"] == "text"
    assert user_message["content"][1] == {
        "type": "image_url",
        "image_url": {"url": "https://cdn.example.com/pet-ai-images/images/image_001.png"},
    }

