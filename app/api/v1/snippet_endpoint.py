from fastapi import APIRouter, HTTPException, Request, Depends
from app.core.config import settings
from app.models.snippet_model import SnippetCreate, SnippetDB
from app.core.rate_limit import RateLimiter
from app.crud.snippet_crud import SnippetOps

snippet_route = APIRouter(prefix=settings.API_V1_STR + "/snippet", tags=["Code Sharing"])

@snippet_route.post("/share", response_model=SnippetDB, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_snippet(snippet_in: SnippetCreate, request: Request):
    try:
        return await SnippetOps.create(request.app.state.mongo_client, snippet_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@snippet_route.get("/{snippet_id}", response_model=SnippetDB)
async def get_snippet(snippet_id: str, request: Request):
    try:
        snippet = await SnippetOps.get(request.app.state.mongo_client, snippet_id)
        
        if not snippet:
            raise HTTPException(status_code=404, detail="Snippet not found")
            
        return snippet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
