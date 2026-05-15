from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import RiskLevel


class HealthRecordResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    analysis_id: str = Field(alias="analysisId")
    image_url: str = Field(alias="imageUrl")
    score: int
    risk_level: RiskLevel = Field(alias="riskLevel")
    risk_text: str = Field(alias="riskText")
    summary: str
    created_at: datetime = Field(alias="createdAt")


class SaveRecordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str = Field(min_length=1, alias="analysisId")


class SaveRecordResult(BaseModel):
    id: str


class PaginationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page: int
    page_size: int = Field(alias="pageSize")
    total: int
    has_more: bool = Field(alias="hasMore")


class RecordListResponse(BaseModel):
    list: list[HealthRecordResponse]
    pagination: PaginationResponse
