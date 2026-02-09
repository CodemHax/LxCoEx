import asyncio

from redis.asyncio import Redis
from app.core.config import settings


class RedisDB:
    redis_client = None
    _lock = asyncio.Lock()
    _initialized: bool = False

    @classmethod
    async def connect(cls):
        if cls._initialized:
            return cls.redis_client

        async with cls._lock:
            if cls._initialized:
                return cls.redis_client

            cls.redis_client = await Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            cls._initialized = True
            return cls.redis_client

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls.redis_client:
                await cls.redis_client.close()
                cls.redis_client = None
                cls._initialized = False



