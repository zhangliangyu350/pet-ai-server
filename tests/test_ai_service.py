import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
import httpx
from dotenv import load_dotenv

from app.services.analysis_sanitizer import sanitize_ai_result
from app.services.ai_service import AI_ANALYSIS_PROMPT
from app.services.ai_service import DoubaoAIClient
from tests.image_fixtures import PNG_1X1

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_POOP_IMAGE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "pet_poop_sample.png"
HARDCODE_SCAN_ROOTS = ("app", "tests", "docs")
HARDCODE_SCAN_ROOT_FILES = (".env.example", "README.md", "pyproject.toml")
REAL_AI_OPT_IN_ENV_NAME = "RUN_REAL_AI_TESTS"
REAL_AI_REQUIRED_ENV_NAMES = ("AI_API_KEY", "AI_API_BASE_URL", "AI_MODEL")
SENSITIVE_LITERAL_PATTERNS = (
    "s" + "k-",
    "AK" + "IA",
    "AI" + "za",
    "xox" + "b-",
    "xox" + "p-",
    "xox" + "a-",
    "Bearer " + "eyJ",
)


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
        model="doubao-vision-pro",
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


@pytest.mark.anyio
class TestDoubaoAIClientRealRequest:
    """真实豆包测试：使用固定宠物便便样本图校验接口和基础识别结果。"""

    def _build_client_from_env(self) -> DoubaoAIClient:
        if os.getenv(REAL_AI_OPT_IN_ENV_NAME) != "1":
            pytest.skip(f"设置 {REAL_AI_OPT_IN_ENV_NAME}=1 后才会发起真实 AI 请求")

        missing_env_names = [name for name in REAL_AI_REQUIRED_ENV_NAMES if not os.getenv(name)]
        if missing_env_names:
            pytest.skip(
                "缺少真实 AI 请求配置，跳过外部请求测试: " + ", ".join(missing_env_names)
            )

        base_url = os.environ["AI_API_BASE_URL"]
        parsed_base_url = urlparse(base_url)
        if parsed_base_url.scheme not in {"http", "https"} or not parsed_base_url.netloc:
            pytest.fail("AI_API_BASE_URL 必须是完整 URL，例如 https://ark.cn-beijing.volces.com/api/v3")

        model = os.environ["AI_MODEL"]
        if os.getenv("AI_PROVIDER") == "doubao" and not model.startswith(("ep-", "ep-m-")):
            pytest.fail(
                "豆包方舟真实请求的 AI_MODEL 应填写推理接入点 ID，通常形如 ep-xxxx 或 ep-m-xxxx；"
                f"当前值是 {model!r}，看起来是底层模型名",
                pytrace=False,
            )

        return DoubaoAIClient(
            api_key=os.environ["AI_API_KEY"],
            base_url=base_url,
            model=model,
            timeout_seconds=60.0,
            max_attempts=1,
        )

    def _build_request_body(self, client: DoubaoAIClient) -> dict:
        image_data_url = client._to_image_data_url(
            image_content=SAMPLE_POOP_IMAGE_PATH.read_bytes(),
            image_type="png",
        )
        return {
            "model": client.model,
            "messages": [
                {"role": "system", "content": AI_ANALYSIS_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "petType": "dog",
                                    "petName": "狗狗",
                                },
                                ensure_ascii=False,
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url},
                        },
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }

    def _redact_image_payload(self, request_body: dict) -> dict:
        printable_body = json.loads(json.dumps(request_body, ensure_ascii=False))
        image_url = printable_body["messages"][1]["content"][1]["image_url"]["url"]
        printable_body["messages"][1]["content"][1]["image_url"]["url"] = (
            image_url[:64] + f"...<base64 omitted, {len(image_url)} chars>"
        )
        return printable_body

    async def test_real_request_returns_expected_result_for_sample_image(self):
        client = self._build_client_from_env()
        request_body = self._build_request_body(client)
        request_url = f"{client.base_url}/chat/completions"

        print("\n真实请求 URL:")
        print(request_url)
        print("\n真实请求 headers:")
        print(json.dumps({"Authorization": "Bearer <hidden>"}, ensure_ascii=False, indent=2))
        print("\n真实请求 body:")
        print(json.dumps(self._redact_image_payload(request_body), ensure_ascii=False, indent=2))

        try:
            async with httpx.AsyncClient(timeout=60.0) as http_client:
                response = await http_client.post(
                    request_url,
                    json=request_body,
                    headers={"Authorization": f"Bearer {client.api_key}"},
                )
        except httpx.HTTPError as exc:
            pytest.fail(f"真实豆包请求网络错误：{exc}", pytrace=False)

        print("\n真实响应 status:")
        print(response.status_code)
        print("\n真实响应 body:")
        print(response.text[:2000])

        if response.status_code >= 400:
            pytest.fail(f"真实豆包请求失败，HTTP 状态码：{response.status_code}", pytrace=False)

        try:
            response_payload = response.json()
            content = response_payload["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            pytest.fail(f"真实豆包响应不是预期 JSON 结构：{exc}", pytrace=False)

        assert isinstance(result, dict)
        clean_result = sanitize_ai_result(result)
        assert 1 <= clean_result.score <= 100
        assert clean_result.risk_level in {"low", "medium", "high", "observe"}
        assert clean_result.summary
        assert clean_result.observation_advice
        assert len(clean_result.observation_advice) <= 5
        assert clean_result.diet_advice
        assert isinstance(clean_result.need_vet, bool)
        assert clean_result.risk_level in {"low", "observe"}
        assert clean_result.score >= 60
        assert clean_result.need_vet is False


def test_project_does_not_contain_obvious_hardcoded_secrets():
    scanned_files = [
        path
        for root_name in HARDCODE_SCAN_ROOTS
        for path in (PROJECT_ROOT / root_name).rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".toml", ".md", ".example"}
    ]
    scanned_files.extend(PROJECT_ROOT / file_name for file_name in HARDCODE_SCAN_ROOT_FILES)

    findings = []
    for path in scanned_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SENSITIVE_LITERAL_PATTERNS:
            if pattern in text:
                findings.append(f"{path.relative_to(PROJECT_ROOT)} contains {pattern}")

    assert findings == []
