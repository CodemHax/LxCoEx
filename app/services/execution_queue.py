import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from app.db.redis import RedisDB
from app.core.excute_engine import execute_code
from app.core.code_sanitizer import sanitize_code
from app.services.logger import logger


class ExecutionQueue:
    QUEUE_KEY = "code_execution:queue"
    RESULTS_PREFIX = "code_execution:result:"
    PROCESSING_KEY = "code_execution:processing"
    
    _instance = None
    _worker_task = None
    _is_running = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def start_worker(cls):
        if cls._is_running:
            return
        
        cls._is_running = True
        cls._worker_task = asyncio.create_task(cls._process_queue())
        logger.info("Queue worker started")
    
    @classmethod
    async def stop_worker(cls):
        cls._is_running = False
        if cls._worker_task:
            cls._worker_task.cancel()
            try:
                await cls._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Queue worker stopped")
    
    @classmethod
    async def add_job(cls, code: str, language: str, timeout: int, stdin: Optional[str] = None) -> str:
        redis = await RedisDB.connect()
        
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "code": code,
            "language": language,
            "timeout": timeout,
            "stdin": stdin,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "result": None
        }
        
        await redis.set(
            f"{cls.RESULTS_PREFIX}{job_id}",
            json.dumps(job_data),
            ex=3600
        )
        
        await redis.rpush(cls.QUEUE_KEY, job_id)
        
        queue_length = await redis.llen(cls.QUEUE_KEY)
        
        logger.info(f"Job {job_id} added to queue. Position: {queue_length}")
        
        return job_id
    
    @classmethod
    async def get_job_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        redis = await RedisDB.connect()
        
        job_data = await redis.get(f"{cls.RESULTS_PREFIX}{job_id}")
        if job_data:
            return json.loads(job_data)
        return None
    
    @classmethod
    async def get_queue_position(cls, job_id: str) -> int:
        redis = await RedisDB.connect()
        
        queue = await redis.lrange(cls.QUEUE_KEY, 0, -1)
        
        try:
            return queue.index(job_id) + 1
        except ValueError:
            return -1
    
    @classmethod
    async def get_queue_length(cls) -> int:
        redis = await RedisDB.connect()
        return await redis.llen(cls.QUEUE_KEY)
    
    @classmethod
    async def _process_queue(cls):
        redis = await RedisDB.connect()
        
        while cls._is_running:
            try:
                result = await redis.blpop(cls.QUEUE_KEY, timeout=1)
                
                if result is None:
                    continue
                
                _, job_id = result
                
                await redis.set(cls.PROCESSING_KEY, job_id)
                
                job_data = await redis.get(f"{cls.RESULTS_PREFIX}{job_id}")
                if not job_data:
                    continue
                
                job = json.loads(job_data)
                
                job["status"] = "processing"
                job["started_at"] = datetime.utcnow().isoformat()
                await redis.set(f"{cls.RESULTS_PREFIX}{job_id}", json.dumps(job), ex=3600)
                
                logger.info(f"Processing job {job_id}")
                
                is_safe, message = sanitize_code(job["code"], job["language"])
                
                if not is_safe:
                    job["status"] = "completed"
                    job["completed_at"] = datetime.utcnow().isoformat()
                    job["result"] = {
                        "error": True,
                        "message": f"Security violation: {message}",
                        "run": {"stdout": "", "stderr": message, "code": 1}
                    }
                else:
                    try:
                        result = await execute_code(
                            job["code"],
                            job["language"],
                            job["timeout"],
                            job["stdin"]
                        )
                        
                        job["status"] = "completed"
                        job["completed_at"] = datetime.utcnow().isoformat()
                        job["result"] = result
                        
                    except Exception as e:
                        logger.error(f"Error executing job {job_id}: {str(e)}")
                        job["status"] = "failed"
                        job["completed_at"] = datetime.utcnow().isoformat()
                        job["result"] = {
                            "error": True,
                            "message": str(e),
                            "run": {"stdout": "", "stderr": str(e), "code": 1}
                        }
                
                await redis.set(f"{cls.RESULTS_PREFIX}{job_id}", json.dumps(job), ex=3600)
                
                await redis.delete(cls.PROCESSING_KEY)
                
                logger.info(f"Job {job_id} completed with status: {job['status']}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker error: {str(e)}")
                await asyncio.sleep(1)
