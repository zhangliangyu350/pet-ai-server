from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PetType = Literal["cat", "dog"]
RiskLevel = Literal["low", "medium", "high", "observe"]


class SubmitAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_url: str = Field(min_length=1, alias="imageUrl")
    image_sha256: str = Field(
        min_length=1,
        alias="imageSha256",
    )
    pet_type: PetType = Field(alias="petType")
    pet_name: str = Field(default="", max_length=20, alias="petName")


class AnalysisResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    score: int
    risk_level: RiskLevel = Field(alias="riskLevel")
    risk_text: str = Field(alias="riskText")
    summary: str
    observation_advice: list[str] = Field(alias="observationAdvice")
    diet_advice: str = Field(alias="dietAdvice")
    need_vet: bool = Field(alias="needVet")
    image_url: str = Field(alias="imageUrl")
    image_sha256: str = Field(alias="imageSha256")
    pet_type: PetType = Field(alias="petType")
    pet_name: str = Field(alias="petName")
    created_at: datetime = Field(alias="createdAt")


class CleanAnalysisResult(BaseModel):
    score: int
    risk_level: RiskLevel
    risk_text: str
    summary: str
    observation_advice: list[str]
    diet_advice: str
    need_vet: bool
