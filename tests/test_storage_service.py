from app.core.config import Settings
from app.services.storage_service import StorageService


class FakeMinioClient:
    def __init__(self, bucket_exists: bool = True) -> None:
        self._bucket_exists = bucket_exists
        self.created_buckets = []
        self.objects = []

    def bucket_exists(self, bucket_name: str) -> bool:
        return self._bucket_exists

    def make_bucket(self, bucket_name: str) -> None:
        self.created_buckets.append(bucket_name)
        self._bucket_exists = True

    def put_object(self, bucket_name: str, object_name: str, data, length: int, content_type: str):
        self.objects.append(
            {
                "bucket_name": bucket_name,
                "object_name": object_name,
                "content": data.read(),
                "length": length,
                "content_type": content_type,
            }
        )


def test_storage_service_saves_to_minio_and_returns_public_url():
    fake_client = FakeMinioClient(bucket_exists=False)
    settings = Settings(
        upload_storage="minio",
        minio_bucket="pet-ai-images",
        public_image_base_url="https://cdn.example.com/pet-ai-images",
    )
    service = StorageService(settings=settings, minio_client=fake_client)

    image_url = service.save_image("image_001", "png", b"image-bytes")

    assert fake_client.created_buckets == ["pet-ai-images"]
    assert fake_client.objects[0]["bucket_name"] == "pet-ai-images"
    assert fake_client.objects[0]["object_name"] == "images/image_001.png"
    assert fake_client.objects[0]["content"] == b"image-bytes"
    assert fake_client.objects[0]["content_type"] == "image/png"
    assert image_url == "https://cdn.example.com/pet-ai-images/images/image_001.png"


def test_storage_service_normalizes_protocol_endpoint():
    endpoint, secure = StorageService._normalize_minio_endpoint("https://minio.example.com")

    assert endpoint == "minio.example.com"
    assert secure is True

