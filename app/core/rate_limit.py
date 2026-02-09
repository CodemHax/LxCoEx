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

        async with redis.pipeline() as pipe:
            try:
                await pipe.incr(key)
                await pipe.expire(key, self.seconds)
                result = await pipe.execute()
                request_count = result[0]
            except Exception:
                return

        if request_count > self.times:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {self.seconds} seconds."
            )
