from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс настроек приложения.
    Все поля могут быть переопределены через переменные окружения.
    """

    # Основные настройки приложения
    app_name: str = "Orbis File Storage"  # Название приложения
    app_version: str = "2.0.0"  # Версия приложения
    debug: bool = False  # Режим отладки (включает дополнительные логи и перезагрузку)

    # Настройки базы данных
    database_url: str = "postgresql+asyncpg://postgres:postgres@db/orbis_storage"  # URL подключения к PostgreSQL

    # Настройки файлового хранилища
    file_storage_path: str = "/app/uploads"  # Путь к директории хранения файлов
    pending_file_prefix: str = "pending_"  # Префикс для временных файлов при загрузке

    # Настройки сервера
    app_host: str = "0.0.0.0"  # Хост для запуска сервера
    app_port: int = 8000  # Порт для запуска сервера

    # Настройки подключения к БД
    db_retries: int = 5  # Количество попыток подключения к БД при запуске
    db_retry_delay: int = 2  # Задержка между попытками подключения в секундах

    model_config = {
        "env_file": ".env",  # Файл с переменными окружения
        "env_file_encoding": "utf-8",  # Кодировка файла
    }


# Глобальный экземпляр настроек
settings = Settings()
