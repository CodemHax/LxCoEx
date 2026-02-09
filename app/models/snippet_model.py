from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SnippetCreate(BaseModel):
    code: str
    language: str
    title: Optional[str] = None


class SnippetDB(SnippetCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    views: int = 0
