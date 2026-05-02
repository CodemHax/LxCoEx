from typing import Optional

from pydantic import BaseModel
from pydantic import field_validator

from app.core.execution_policy import normalize_language, validate_stdin, validate_timeout



class CodeInput(BaseModel):
    code: str
    language: str
    timeout: float | int = 3000
    stdin: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language(value)

    @field_validator("timeout")
    @classmethod
    def validate_timeout_value(cls, value: float | int) -> int:
        return validate_timeout(value)

    @field_validator("stdin")
    @classmethod
    def validate_stdin_value(cls, value: Optional[str]) -> str:
        return validate_stdin(value)
