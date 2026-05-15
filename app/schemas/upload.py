from pydantic import BaseModel, ConfigDict, Field


class UploadImageResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_url: str = Field(serialization_alias="imageUrl")
    image_sha256: str = Field(serialization_alias="imageSha256")
    width: int
    height: int
    size: int

