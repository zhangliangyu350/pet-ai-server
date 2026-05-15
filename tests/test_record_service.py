from app.models.analysis import Analysis
from app.models.user import User
from app.services.record_service import RecordService
from tests.db_helpers import build_sqlite_session
from tests.fakes import FakeRedis


def add_user_and_analysis(db):
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
    db.add_all([user, analysis])
    db.commit()


def test_record_service_saves_lists_and_deletes_record():
    db = build_sqlite_session()
    redis = FakeRedis()
    add_user_and_analysis(db)
    service = RecordService(db=db, redis_client=redis)

    saved = service.save_record(user_id="user_001", analysis_id="analysis_001")
    listed = service.list_records(user_id="user_001", page=1, page_size=20)
    recent = service.get_recent_record(user_id="user_001")
    service.delete_record(user_id="user_001", record_id=saved.id)
    listed_after_delete = service.list_records(user_id="user_001", page=1, page_size=20)

    assert saved.id.startswith("record_")
    assert listed.pagination.total == 1
    assert recent.analysis_id == "analysis_001"
    assert listed_after_delete.pagination.total == 0


def test_record_service_save_is_idempotent():
    db = build_sqlite_session()
    redis = FakeRedis()
    add_user_and_analysis(db)
    service = RecordService(db=db, redis_client=redis)

    first = service.save_record(user_id="user_001", analysis_id="analysis_001")
    second = service.save_record(user_id="user_001", analysis_id="analysis_001")

    assert first.id == second.id

