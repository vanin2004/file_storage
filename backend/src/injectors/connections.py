import os
import time
from functools import lru_cache
from typing import AsyncGenerator, Callable

import sqlalchemy_utils as sa_utils
from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.config import fs_config, pg_config
from src.models import Base
from src.services import AsyncFileService


class DatabaseError(Exception):
    """Базовый класс для ошибок бд"""

    pass


class DatabaseConnectionError(DatabaseError):
    """Ошибка подключения к базе данных"""

    pass


class DatabaseOperationError(DatabaseError):
    """Ошибка выполнения операции с базой данных"""

    pass


@lru_cache(maxsize=1)
def create_engine():
    """Создает и кэширует асинхронный движок базы данных."""

    if sa_utils.database_exists(pg_config.database_url):
        sa_utils.create_database(pg_config.database_url)

    config = pg_config
    return create_async_engine(config.database_url, echo=config.debug_mode)


@lru_cache(maxsize=1)
def create_database() -> async_sessionmaker[AsyncSession]:
    """Создает и кэширует фабрику асинхронных сессий."""

    engine = create_engine()
    return async_sessionmaker(bind=engine)


async def initialize_database() -> None:
    """Создает таблицы в базе данных при старте приложения (асинхронно)."""

    config = pg_config
    engine = create_engine()
    retries = config.retries
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except SQLAlchemyError as e:
            if attempt < retries - 1:
                time.sleep(config.retry_delay_sec)
            else:
                raise DatabaseConnectionError(
                    f"Error creating database after {retries} attempts: {e}"
                )


async def get_db(
    async_session: async_sessionmaker = Depends(create_database),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор сессий базы данных для использования в FastAPI зависимостях.
    Обеспечивает автоматический commit при успехе и rollback при ошибке.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise DatabaseOperationError(
                "Database transaction failed and was rolled back."
            )
        except Exception:
            await session.rollback()
            raise


@lru_cache(maxsize=1)
def create_file_storage() -> Callable[[], AsyncFileService]:
    config = fs_config
    os.makedirs(config.file_storage_path, exist_ok=True)
    return lambda: AsyncFileService(
        config=fs_config,
    )


async def get_fs(
    async_session: Callable[[], AsyncFileService] = Depends(create_file_storage),
) -> AsyncFileService:
    return async_session()
