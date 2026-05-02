from typing import Optional
from pydantic import BaseModel


class RuntimeSpec(BaseModel):
    language: str
    runtime: str
    aliases: tuple[str, ...] = ()

    model_config = {"frozen": True}


class RuntimeInfo(BaseModel):
    language: str
    version: str
    aliases: list[str]
    runtime: str
    available: bool
    missing_commands: list[str]
    engine: str


class CompileResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    code: int = 0


class RunResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    code: int = 0


class ExecutionResult(BaseModel):
    language: str
    version: str
    engine: str
    error: bool
    message: str
    compile: CompileResult
    run: RunResult
