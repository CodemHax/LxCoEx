from fastapi import Request

async def get_mongo_client(request: Request):
    return request.app.state.mongo_client


async def get_redis_client(request: Request):
    return request.app.state.redis_client

