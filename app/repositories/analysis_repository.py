from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        """创建绑定到数据库会话的分析仓储。"""
        self.db = db

    def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """按主键返回分析记录。"""
        return self.db.get(Analysis, analysis_id)

    def get_latest_by_sha256(self, image_sha256: str) -> Optional[Analysis]:
        """按重复图片指纹返回最新分析结果。"""
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
        """返回用户或游客身份下最近一次分析。"""
        statement = select(Analysis).order_by(desc(Analysis.created_at)).limit(1)
        if user_id:
            statement = statement.where(Analysis.user_id == user_id)
        elif guest_id:
            statement = statement.where(Analysis.guest_id == guest_id)
        else:
            return None
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, analysis: Analysis) -> Analysis:
        """在当前事务中持久化新的分析记录。"""
        self.db.add(analysis)
        self.db.flush()
        return analysis
