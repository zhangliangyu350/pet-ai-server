import pytest

from app.core.exceptions import BusinessError, ErrorCode
from app.models.analysis import Analysis
from app.models.image_asset import ImageAsset
from app.schemas.analysis import SubmitAnalysisRequest
from app.services.analysis_service import AnalysisService
from tests.db_helpers import build_sqlite_session
from tests.fakes import FakeRedis
from tests.image_fixtures import PNG_1X1


class FakeAIClient:
    def __init__(self, raw_result: dict = None, should_fail: bool = False) -> None:
        self.raw_result = raw_result or {
            "score": 82,
            "riskLevel": "low",
            "summary": "状态较稳定",
            "observationAdvice": ["继续观察"],
            "dietAdvice": "保持饮水",
            "needVet": False,
        }
        self.should_fail = should_fail
        self.calls = 0

    async def analyze_poop_image(
        self,
        image_content: bytes,
        image_type: str,
        pet_type: str,
        pet_name: str = "",
    ):
        self.calls += 1
        if self.should_fail:
            raise BusinessError(ErrorCode.analysis_failed)
        assert image_content == PNG_1X1
        assert image_type == "png"
        return self.raw_result


def build_payload(sha256: str = "sha256_001") -> SubmitAnalysisRequest:
    return SubmitAnalysisRequest(
        imageUrl="http://localhost/static/uploads/image_001.png",
        imageSha256=sha256,
        petType="dog",
        petName="狗狗",
    )


class FakeStorageService:
    def read_image(self, image_url: str):
        assert image_url == "http://localhost/static/uploads/image_001.png"
        return PNG_1X1, "png"


def add_uploaded_image(db, sha256: str = "sha256_001") -> None:
    db.add(
        ImageAsset(
            id=f"image_{sha256}",
            image_url="http://localhost/static/uploads/image_001.png",
            image_sha256=sha256,
            width=1,
            height=1,
            size=len(PNG_1X1),
        )
    )
    db.commit()


@pytest.mark.anyio
async def test_submit_analysis_calls_ai_and_saves_guest_recent():
    db = build_sqlite_session()
    add_uploaded_image(db)
    redis = FakeRedis()
    ai_client = FakeAIClient()
    service = AnalysisService(
        db=db,
        redis_client=redis,
        ai_client=ai_client,
        storage_service=FakeStorageService(),
    )

    result = await service.submit_analysis(payload=build_payload(), guest_id="guest_001")

    assert result.id.startswith("analysis_")
    assert result.risk_level == "low"
    assert ai_client.calls == 1
    assert redis.get("guest:recent:guest_001") == result.id


@pytest.mark.anyio
async def test_submit_analysis_uses_sha256_cache():
    db = build_sqlite_session()
    add_uploaded_image(db)
    redis = FakeRedis()
    ai_client = FakeAIClient()
    service = AnalysisService(
        db=db,
        redis_client=redis,
        ai_client=ai_client,
        storage_service=FakeStorageService(),
    )

    first = await service.submit_analysis(payload=build_payload(), guest_id="guest_001")
    second = await service.submit_analysis(payload=build_payload(), guest_id="guest_002")

    assert first.id == second.id
    assert ai_client.calls == 1


@pytest.mark.anyio
async def test_submit_analysis_blocks_too_frequent():
    db = build_sqlite_session()
    add_uploaded_image(db, "sha256_001")
    add_uploaded_image(db, "sha256_002")
    redis = FakeRedis()
    service = AnalysisService(
        db=db,
        redis_client=redis,
        ai_client=FakeAIClient(),
        storage_service=FakeStorageService(),
    )

    await service.submit_analysis(payload=build_payload("sha256_001"), guest_id="guest_001")

    with pytest.raises(BusinessError) as exc_info:
        await service.submit_analysis(payload=build_payload("sha256_002"), guest_id="guest_001")

    assert exc_info.value.code == ErrorCode.analysis_too_frequent


@pytest.mark.anyio
async def test_submit_analysis_fails_without_identity():
    db = build_sqlite_session()
    redis = FakeRedis()
    service = AnalysisService(
        db=db,
        redis_client=redis,
        ai_client=FakeAIClient(),
        storage_service=FakeStorageService(),
    )

    with pytest.raises(BusinessError) as exc_info:
        await service.submit_analysis(payload=build_payload())

    assert exc_info.value.code == ErrorCode.auth_required


@pytest.mark.anyio
async def test_submit_analysis_maps_ai_failure():
    db = build_sqlite_session()
    add_uploaded_image(db)
    redis = FakeRedis()
    service = AnalysisService(
        db=db,
        redis_client=redis,
        ai_client=FakeAIClient(should_fail=True),
        storage_service=FakeStorageService(),
    )

    with pytest.raises(BusinessError) as exc_info:
        await service.submit_analysis(payload=build_payload(), guest_id="guest_001")

    assert exc_info.value.code == ErrorCode.analysis_failed


@pytest.mark.anyio
async def test_submit_analysis_reads_existing_db_cache():
    db = build_sqlite_session()
    redis = FakeRedis()
    db.add(
        Analysis(
            id="analysis_existing",
            image_url="http://localhost/static/uploads/image_001.png",
            image_sha256="sha256_existing",
            pet_type="dog",
            pet_name="狗狗",
            score=90,
            risk_level="low",
            risk_text="低风险",
            summary="状态较稳定",
            observation_advice=["继续观察"],
            diet_advice="保持饮水",
            need_vet=False,
            raw_ai_result={},
        )
    )
    db.commit()
    ai_client = FakeAIClient()
    service = AnalysisService(
        db=db,
        redis_client=redis,
        ai_client=ai_client,
        storage_service=FakeStorageService(),
    )

    result = await service.submit_analysis(payload=build_payload("sha256_existing"), guest_id="guest_001")

    assert result.id == "analysis_existing"
    assert ai_client.calls == 0
