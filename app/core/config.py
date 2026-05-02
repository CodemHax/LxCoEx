from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "LiCoEx API"
    API_V1_STR: str = "/api/v1"

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "licoex_db"
    REDIS_URL: str = "redis://localhost:6379"

    EXECUTION_TMP_DIR: Optional[str] = None
    EXECUTION_COMPILE_TIMEOUT_MS: int = 10000
    EXECUTION_MAX_OUTPUT_BYTES: int = 32768

    EXECUTION_DOCKER_BINARY: str = "docker"
    EXECUTION_SANDBOX_IMAGE: str = "licoex-sandbox:latest"
    EXECUTION_SANDBOX_UID: int = 65534
    EXECUTION_SANDBOX_GID: int = 65534
    EXECUTION_SANDBOX_MEMORY: str = "256m"
    EXECUTION_SANDBOX_MEMORY_SWAP: str = "256m"
    EXECUTION_SANDBOX_CPUS: float = 1.0
    EXECUTION_SANDBOX_PIDS_LIMIT: int = 64
    EXECUTION_SANDBOX_NOFILE: int = 64
    EXECUTION_SANDBOX_FSIZE: int = 1048576
    EXECUTION_SANDBOX_TMP_SIZE: str = "64m"
    EXECUTION_SANDBOX_INPUT_SIZE: str = "16m"
    EXECUTION_SANDBOX_WORKSPACE_SIZE: str = "128m"

    class Config:
        case_sensitive = True


settings = Settings()
