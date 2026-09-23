import json
from typing import Optional, Any
from redis.asyncio import Redis
from app.core.config import settings

class RedisCacheBackend:
    def __init__(self, redis_url: str, ttl_sec: int = 3600):
        self.ttl_sec = ttl_sec
        self.redis = Redis.from_url(redis_url, decode_responses=True)

    async def set(self, key: str, value: dict):
        await self.redis.set(key, json.dumps(value), ex=self.ttl_sec)


    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None


    async def delete(self, key: str):
        await self.redis.delete(key)


cache = RedisCacheBackend(redis_url=settings.CACHE_URL,ttl_sec=360)