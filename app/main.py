from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.v1.excuter_endpoint import ex_route
from app.api.v1.snippet_endpoint import snippet_route
from app.db.mongo import MONGODatabase
from app.db.redis import RedisDB
from app.services.logger import logger
from app.services.execution_queue import ExecutionQueue

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    mongo_client = await MONGODatabase.connect()
    logger.info("Connected to MongoDB")

    redis_client = await RedisDB.connect()
    logger.info("Connected to Redis")

    await ExecutionQueue.start_worker()
    logger.info("Execution queue worker started")

    app.state.mongo_client = mongo_client
    app.state.redis_client = redis_client

    yield
    
    logger.info("Shutting down...")
    
    await ExecutionQueue.stop_worker()
    logger.info("Execution queue worker stopped")
    
    await MONGODatabase.close()
    logger.info("Disconnected from MongoDB")
    await RedisDB.close()
    logger.info("Disconnected from Redis")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ex_route)
app.include_router(snippet_route)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
