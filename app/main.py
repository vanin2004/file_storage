from fastapi import FastAPI
import uvicorn
import sys
import os

from app.core.localstorage import create_file_storage_directory
from app.core.database import create_database
from app.core.settings import settings

# Добавляем родительскую директорию в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.api import router as api_router
from app.exceptions.handlers import (
    resource_not_found_handler,
    resource_already_exists_handler,
    database_error_handler,
    local_storage_unavailable_handler,
    local_storage_error_handler,
    global_exception_handler,
)
from app.exceptions.service import ResourceNotFoundError, ResourceAlreadyExistsError
from app.exceptions.database import DatabaseError
from app.exceptions.localstorage import LocalStorageError, LocalStorageUnavailableError

# Инициализация приложения FastAPI с настройками из settings
app = FastAPI(
    title=settings.app_name, version=settings.app_version, debug=settings.debug
)

# Регистрация обработчиков ошибок
app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
app.add_exception_handler(ResourceAlreadyExistsError, resource_already_exists_handler)
app.add_exception_handler(DatabaseError, database_error_handler)
app.add_exception_handler(LocalStorageUnavailableError, local_storage_unavailable_handler)
app.add_exception_handler(LocalStorageError, local_storage_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Регистрация обработчиков событий запуска
# Создаем директорию для хранения файлов, если она не существует
app.add_event_handler("startup", create_file_storage_directory)
# Создаем таблицы в базе данных (если не существуют)
app.add_event_handler("startup", create_database)

# Подключение маршрутов API
app.include_router(api_router)


if __name__ == "__main__":
    # Запуск сервера uvicorn для локальной разработки
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug",
    )
