"""
Основной модуль приложения Orbis File Storage.
Инициализирует FastAPI приложение, регистрирует маршруты и обработчики ошибок.
"""

from fastapi import FastAPI
import uvicorn

from app.core.localstorage import create_file_storage_directory
from app.core.database import create_database
from app.core.settings import settings

from app.api import router as api_router
from app.exceptions.handlers import (
    resource_not_found_handler,
    resource_already_exists_handler,
    database_error_handler,
    local_storage_unavailable_handler,
    local_storage_error_handler,
    global_exception_handler,
)
from app.exceptions.service import (
    ServiceFileNotFoundError,
    ServiceFileAlreadyExistsError,
)
from app.exceptions.database import DatabaseError
from app.exceptions.localstorage import LocalStorageError, LocalStorageUnavailableError

app = FastAPI(
    title=settings.app_name, version=settings.app_version, debug=settings.debug
)

app.add_exception_handler(ServiceFileNotFoundError, resource_not_found_handler)
app.add_exception_handler(
    ServiceFileAlreadyExistsError, resource_already_exists_handler
)
app.add_exception_handler(DatabaseError, database_error_handler)
app.add_exception_handler(
    LocalStorageUnavailableError, local_storage_unavailable_handler
)
app.add_exception_handler(LocalStorageError, local_storage_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_event_handler("startup", create_file_storage_directory)
app.add_event_handler("startup", create_database)

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="debug",
    )
