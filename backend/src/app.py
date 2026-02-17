"""
Основной модуль приложения Orbis File Storage.
Инициализирует FastAPI приложение, регистрирует маршруты и обработчики ошибок.
"""

from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

from src.routers import router as api_router
from src.routers import (
    resource_not_found_handler,
    resource_already_exists_handler,
    # database_error_handler,
    # local_storage_unavailable_handler,
    # local_storage_error_handler,
)
from src.services.file_holder_service import (
    ServiceFileNotFoundError,
    ServiceFileAlreadyExistsError,
)

from src.injectors import (
    create_database,
    initialize_database,
    create_file_storage,
)

from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database()
    await initialize_database()
    create_file_storage()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)


app.add_exception_handler(ServiceFileNotFoundError, resource_not_found_handler)
app.add_exception_handler(
    ServiceFileAlreadyExistsError, resource_already_exists_handler
)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="debug",
    )
