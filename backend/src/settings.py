from pydantic_settings import BaseSettings

from src.config.pg import PgConfig
from src.config.fs import FsConfig


class Settings(BaseSettings):
    """
    Класс настроек приложения.
    Все поля могут быть переопределены через переменные окружения.
    """

    # Основные настройки приложения
    app_name: str = "Orbis File Storage"
    app_version: str = "2.0.0"
    debug: bool = False

    # Настройки базы данных
    database_url: str = "postgresql+asyncpg://postgres:postgres@db/orbis_storage"

    # Настройки файлового хранилища
    file_storage_path: str = "/app/uploads"
    pending_file_prefix: str = "pending_"

    # Настройки сервера
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Настройки подключения к БД
    db_retries: int = 5
    db_retry_delay: int = 2

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Глобальный экземпляр настроек
settings = Settings()

pg_config = PgConfig(
    database_url=settings.database_url,
    retries=settings.db_retries,
    retry_delay_sec=settings.db_retry_delay,
    debug_mode=settings.debug,
)

fs_config = FsConfig(
    file_storage_path=settings.file_storage_path,
    pending_file_prefix=settings.pending_file_prefix,
)
