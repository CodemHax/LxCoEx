from fastapi import HTTPException, Request, Depends
from redis.asyncio import Redis

from app.api.deps import get_redis_client


class RateLimiter:
    def __init__(self, times: int = 30, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request, redis: Redis = Depends(get_redis_client)):
        if not redis:
            return

        client_ip = request.client.host
        key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            request_count = await redis.incr(key)
            if request_count == 1:
                await redis.expire(key, self.seconds)
            else:
                ttl = await redis.ttl(key)
                if ttl == -1:
                    await redis.expire(key, self.seconds)
        except Exception:
            return

        if request_count > self.times:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {self.seconds} seconds."
            )
