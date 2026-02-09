from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "LiCoEx API"
    API_V1_STR: str = "/api/v1"

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "licoex_db"
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        case_sensitive = True


settings = Settings()