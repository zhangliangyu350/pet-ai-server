import json
import logging

import httpx

from app.core.config import get_settings
from app.core.exceptions import BusinessError, ErrorCode

logger = logging.getLogger(__name__)

AI_ANALYSIS_PROMPT = """
你是宠物健康参考助手。请根据宠物便便图片信息返回 JSON。
必须避免诊断、治疗、处方、药物建议等医疗高风险表达。
仅输出 JSON，字段包含 score、riskLevel、summary、observationAdvice、dietAdvice、needVet。
"""


class DeepSeekAIClient:
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        timeout_seconds: float = 20.0,
        max_attempts: int = 2,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.ai_api_key
        self.base_url = (base_url if base_url is not None else settings.ai_api_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max(max_attempts, 1)

    async def analyze_poop_image(
        self,
        image_url: str,
        pet_type: str,
        pet_name: str = "",
    ) -> dict:
        if not self.api_key or not self.base_url:
            raise BusinessError(ErrorCode.analysis_busy)

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": AI_ANALYSIS_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "imageUrl": image_url,
                            "petType": pet_type,
                            "petName": pet_name,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response_payload = await self._post_with_retry(payload=payload, headers=headers)

        try:
            content = response_payload["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise BusinessError(ErrorCode.analysis_failed) from None

    async def _post_with_retry(self, payload: dict, headers: dict) -> dict:
        last_error = None
        for attempt in range(self.max_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                raise BusinessError(ErrorCode.analysis_busy) from None
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                logger.warning("AI analysis request failed on attempt %s", attempt + 1)

        raise BusinessError(ErrorCode.analysis_failed) from last_error
