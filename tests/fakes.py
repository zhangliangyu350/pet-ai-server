class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.expirations = {}

    def get(self, key: str):
        return self.values.get(key)

    def set(self, key: str, value) -> None:
        self.values[key] = str(value)

    def setex(self, key: str, ttl_seconds: int, value) -> None:
        self.values[key] = value
        self.expirations[key] = ttl_seconds

    def incr(self, key: str) -> int:
        value = int(self.values.get(key, 0)) + 1
        self.values[key] = str(value)
        return value

    def expireat(self, key: str, timestamp: int) -> None:
        self.expirations[key] = timestamp

