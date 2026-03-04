from typing import Optional


class MemoryStorage:
    """In-memory storage for tests. Satisfies the ReportStorage protocol."""

    def __init__(self):
        self._objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = (data, content_type)

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"http://fake-storage/{key}"

    async def delete(self, key: str) -> None:
        self._objects.pop(key, None)

    def get_object(self, key: str) -> Optional[bytes]:
        obj = self._objects.get(key)
        return obj[0] if obj else None
