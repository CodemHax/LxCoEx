import asyncio
from typing import Dict, List, Any

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


class MONGODatabase:
    mongo_client = None
    _lock = asyncio.Lock()
    _initialized: bool = False
    _default_db_name: str = settings.MONGODB_DB_NAME

    @classmethod
    def set_client(cls, client: AsyncIOMotorClient):
        cls.mongo_client = client
        cls._initialized = True

    @classmethod
    async def connect(cls):
        if cls._initialized:
            return cls.mongo_client

        async with cls._lock:
            if cls._initialized:
                return cls.mongo_client

            cls.mongo_client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )

            try:
                await cls.mongo_client.admin.command('ping')
            except Exception:
                cls.mongo_client = None
                raise
            cls._initialized = True
            return cls.mongo_client

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls.mongo_client:
                cls.mongo_client.close()
                cls.mongo_client = None
                cls._initialized = False

    @classmethod
    async def insert_one(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, document: Dict[str, Any]):
        db = mongodb_instance[db_name]
        return await db[collection].insert_one(document)

    @classmethod
    async def insert_many(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, documents: List[Dict[str, Any]]):
        db = mongodb_instance[db_name]
        return await db[collection].insert_many(documents)

    @classmethod
    async def find_one(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, query: Dict[str, Any]):
        db = mongodb_instance[db_name]
        return await db[collection].find_one(query)

    @classmethod
    async def find_many(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, query: Dict[str, Any], limit: int = 0):
        db = mongodb_instance[db_name]
        cursor = db[collection].find(query)
        if limit > 0:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)

    @classmethod
    async def update_one(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, query: Dict[str, Any], update: Dict[str, Any]):
        db = mongodb_instance[db_name]
        return await db[collection].update_one(query, {"$set": update})

    @classmethod
    async def update_many(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, query: Dict[str, Any], update: Dict[str, Any]):
        db = mongodb_instance[db_name]
        return await db[collection].update_many(query, {"$set": update})

    @classmethod
    async def delete_one(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, query: Dict[str, Any]):
        db = mongodb_instance[db_name]
        return await db[collection].delete_one(query)

    @classmethod
    async def delete_many(cls, mongodb_instance: AsyncIOMotorClient, db_name: str, collection: str, query: Dict[str, Any]):
        db = mongodb_instance[db_name]
        return await db[collection].delete_many(query)
