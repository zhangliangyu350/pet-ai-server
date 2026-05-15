from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        return self.db.get(Analysis, analysis_id)

    def get_latest_by_sha256(self, image_sha256: str) -> Optional[Analysis]:
        statement = (
            select(Analysis)
            .where(Analysis.image_sha256 == image_sha256)
            .order_by(desc(Analysis.created_at))
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_recent_for_identity(
        self,
        user_id: str = None,
        guest_id: str = None,
    ) -> Optional[Analysis]:
        statement = select(Analysis).order_by(desc(Analysis.created_at)).limit(1)
        if user_id:
            statement = statement.where(Analysis.user_id == user_id)
        elif guest_id:
            statement = statement.where(Analysis.guest_id == guest_id)
        else:
            return None
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, analysis: Analysis) -> Analysis:
        self.db.add(analysis)
        self.db.flush()
        return analysis

