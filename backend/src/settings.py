from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс настроек приложения.
    Все поля могут быть переопределены через переменные окружения.
    """

    # Основные настройки приложения
    app_name: str = "Orbis File Storage"
    app_version: str = "3.0.0"
    debug: bool = False

    # Настройки базы данных
    database_url: str = "postgresql+asyncpg://postgres:postgres@db/orbis_storage"

    # Настройки файлового хранилища
    file_storage_path: str = "/app/uploads"

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
