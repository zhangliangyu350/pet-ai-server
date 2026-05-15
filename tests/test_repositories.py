from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.analysis import Analysis
from app.models.health_record import HealthRecord
from app.models.image_asset import ImageAsset
from app.models.user import User
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.record_repository import RecordRepository
from app.repositories.user_repository import UserRepository


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_user_repository_upserts_by_openid():
    db = build_session()
    repository = UserRepository(db)

    created = repository.upsert_wechat_user(user_id="user_001", openid="openid_001")
    updated = repository.upsert_wechat_user(
        user_id="ignored",
        openid="openid_001",
        nickname="新用户",
    )

    assert created.id == "user_001"
    assert updated.id == "user_001"
    assert updated.nickname == "新用户"


def test_image_repository_gets_by_sha256():
    db = build_session()
    repository = ImageRepository(db)
    image = ImageAsset(
        id="image_001",
        image_url="https://example.com/image.jpg",
        image_sha256="sha256_001",
        width=100,
        height=80,
        size=1024,
    )

    repository.create(image)

    assert repository.get_by_sha256("sha256_001").id == "image_001"


def test_analysis_repository_gets_latest_by_sha256():
    db = build_session()
    repository = AnalysisRepository(db)
    analysis = Analysis(
        id="analysis_001",
        image_url="https://example.com/image.jpg",
        image_sha256="sha256_001",
        pet_type="dog",
        pet_name="狗狗",
        score=82,
        risk_level="low",
        risk_text="低风险",
        summary="状态较稳定",
        observation_advice=["继续观察"],
        diet_advice="保持饮水",
        need_vet=False,
        raw_ai_result={},
    )

    repository.create(analysis)

    assert repository.get_latest_by_sha256("sha256_001").id == "analysis_001"


def test_record_repository_lists_active_records():
    db = build_session()
    user = User(id="user_001", openid="openid_001")
    analysis = Analysis(
        id="analysis_001",
        user_id="user_001",
        image_url="https://example.com/image.jpg",
        image_sha256="sha256_001",
        pet_type="dog",
        pet_name="狗狗",
        score=82,
        risk_level="low",
        risk_text="低风险",
        summary="状态较稳定",
        observation_advice=["继续观察"],
        diet_advice="保持饮水",
        need_vet=False,
        raw_ai_result={},
    )
    record = HealthRecord(id="record_001", user_id="user_001", analysis_id="analysis_001")
    db.add_all([user, analysis, record])
    db.flush()

    repository = RecordRepository(db)
    records, total = repository.list_for_user(user_id="user_001", page=1, page_size=20)

    assert total == 1
    assert records[0].id == "record_001"

