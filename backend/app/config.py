import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # MySQL
    DB_HOST: str = Field(default="127.0.0.1")
    DB_PORT: int = Field(default=3306)
    DB_USER: str = Field(default="root")
    DB_PASSWORD: str = Field(default="root")
    DB_NAME: str = Field(default="db_asistencia")
    DB_SSL: bool = Field(default=False)

    # API Externa DNI
    DNI_API_BASE_URL: str = Field(default="https://api.ejemplo.com/dni?numero=")
    DNI_API_TOKEN: str = Field(default="")
    DNI_API_TIMEOUT_SECONDS: float = Field(default=5.0)

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ENVIRONMENT: str = Field(default="development")
    CORS_ORIGINS: List[str] = Field(default=["*"])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
