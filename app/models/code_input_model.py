from typing import Literal, Optional

from pydantic import BaseModel



class CodeInput(BaseModel):
    code: str
    language: Literal["python", "go", "javascript", "java", "c", "cpp", "typescript"]
    timeout: float | int
    stdin: Optional[str] = None
