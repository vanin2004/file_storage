"""
Основной модуль приложения Orbis File Storage.
Инициализирует FastAPI приложение, регистрирует маршруты и обработчики ошибок.
"""

from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

from src.routers.api import router as api_router
from src.routers.handlers import (
    resource_not_found_handler,
    resource_already_exists_handler,
    database_error_handler,
    local_storage_unavailable_handler,
    local_storage_error_handler,
    global_exception_handler,
)
from src.services.file_holder_service import (
    ServiceFileNotFoundError,
    ServiceFileAlreadyExistsError,
)

from src.injectors.database import create_database, initialize_database
from src.injectors.localstorage import create_file_storage

from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Инициализация  psql")
    create_database()
    await initialize_database()
    print("Инициализация  файлового хранилища")
    create_file_storage()
    print("инициализация завершена, запуск приложения")
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)


app.add_exception_handler(ServiceFileNotFoundError, resource_not_found_handler)
app.add_exception_handler(
    ServiceFileAlreadyExistsError, resource_already_exists_handler
)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="debug",
    )
