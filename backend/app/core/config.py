import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve absolute path to .env in the project root directory
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))
_env_file_path = os.path.join(_project_root, ".env")


class Settings(BaseSettings):
    APP_ENV: str = "development"
    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE_MB: int = 20

    POSTGRES_USER: str = "medapp"
    POSTGRES_PASSWORD: str = "medpassword"
    POSTGRES_DB: str = "medical_monitor"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    USE_SQLITE: bool = True

    DATABASE_URL: Optional[str] = None

    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "medtoken"
    INFLUXDB_ORG: str = "hospital"
    INFLUXDB_BUCKET: str = "vitals"

    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "hospital/bed/+/vitals"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "medadmin"
    MINIO_SECRET_KEY: str = "medsecret123"
    MINIO_BUCKET: str = "medical-files"
    MINIO_SECURE: bool = False

    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_MODEL: str = "gpt-4o"

    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # Default to 7 days to prevent frequent logouts

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_dsn(self) -> str:
        if self.USE_SQLITE:
            return "sqlite:///./medical_monitor.db"
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        return self.postgres_dsn

    class Config:
        env_file = _env_file_path
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

