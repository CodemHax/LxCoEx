import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.core.excute_engine import get_runtime
from app.core.code_sanitizer import sanitize_code, get_blocked_modules, get_blocked_functions
from app.core.templates import get_template, get_all_templates, get_available_languages
from app.core.exceptions import SecurityError, JobNotFoundError, CodeExecutionError
from app.models.code_input_model import CodeInput
from app.services.logger import logger
from app.services.execution_queue import ExecutionQueue

ex_route = APIRouter(prefix=settings.API_V1_STR + "/core")


@ex_route.post("/execute", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def execute(model: CodeInput):
    try:
        code = model.code
        language = model.language
        timeout = model.timeout
        stdin = model.stdin
        
        is_safe, message = sanitize_code(code, language)
        if not is_safe:
            logger.warning(f"Code rejected by sanitizer: {message}")
            raise SecurityError(message)
        
        job_id = await ExecutionQueue.add_job(code, language, timeout, stdin)
        queue_length = await ExecutionQueue.get_queue_length()
        
        logger.info(f"Job {job_id} added to queue")
        
        return JSONResponse({
            "job_id": job_id,
            "status": "queued",
            "queue_position": queue_length,
            "message": "Job added to queue. Poll /job/{job_id} for results."
        })
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ex_route.get("/job/{job_id}")
async def get_job_status(job_id: str):
    try:
        job = await ExecutionQueue.get_job_status(job_id)
        
        if not job:
            raise JobNotFoundError(job_id)
        
        response = {
            "job_id": job_id,
            "status": job["status"],
            "created_at": job.get("created_at"),
        }
        
        if job["status"] == "queued":
            position = await ExecutionQueue.get_queue_position(job_id)
            response["queue_position"] = position
        elif job["status"] in ["completed", "failed"]:
            response["result"] = job.get("result")
            response["completed_at"] = job.get("completed_at")
        
        return JSONResponse(response)
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ex_route.post("/execute-sync", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def execute_sync(model: CodeInput):
    try:
        code = model.code
        language = model.language
        timeout = model.timeout
        stdin = model.stdin
        
        is_safe, message = sanitize_code(code, language)
        if not is_safe:
            logger.warning(f"Code rejected by sanitizer: {message}")
            raise SecurityError(message)
        
        job_id = await ExecutionQueue.add_job(code, language, timeout, stdin)
        
        max_wait = 30
        poll_interval = 0.5
        elapsed = 0
        
        while elapsed < max_wait:
            job = await ExecutionQueue.get_job_status(job_id)
            
            if job and job["status"] in ["completed", "failed"]:
                result = job.get("result", {})
                return JSONResponse(result)
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        return JSONResponse({
            "error": True,
            "message": "Execution timeout - job still in queue",
            "job_id": job_id,
            "run": {"stdout": "", "stderr": "Job still processing.", "code": -1}
        })
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ex_route.get("/queue/status")
async def get_queue_status():
    try:
        queue_length = await ExecutionQueue.get_queue_length()
        return JSONResponse({
            "queue_length": queue_length,
            "message": f"{queue_length} job(s) in queue"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ex_route.get("/get-runtimes")
async def get_runtimes():
    try:
        runtimes = await get_runtime()
        return JSONResponse(content=runtimes, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ex_route.get("/template/{language}")
async def get_language_template(language: str):
    template = get_template(language)
    if not template:
        raise HTTPException(status_code=404, detail=f"No template found for language: {language}")
    return JSONResponse({
        "language": language,
        "template": template
    })


@ex_route.get("/templates")
async def get_templates():
    templates = get_all_templates()
    languages = get_available_languages()
    return JSONResponse({
        "templates": templates,
        "languages": languages
    })
