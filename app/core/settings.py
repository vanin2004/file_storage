from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Orbis File Storage"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@db/orbis_storage"
    file_storage_path: str = "/app/app/uploads"
    pending_file_prefix: str = "pending_"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
