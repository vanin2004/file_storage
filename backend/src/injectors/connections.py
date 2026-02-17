from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import AsyncGenerator
import time
from fastapi import Depends
from functools import lru_cache

from src.settings import pg_config

from src.models.declarative_base import Base

import os
from typing import Callable
from src.services import AsyncFileSession
from src.settings import fs_config


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
def create_file_storage() -> Callable[[], AsyncFileSession]:
    config = fs_config
    os.makedirs(config.file_storage_path, exist_ok=True)
    return lambda: AsyncFileSession(
        storage_path=config.file_storage_path,
        pending_prefix=config.pending_file_prefix,
    )


async def get_fs(
    async_session: Callable[[], AsyncFileSession] = Depends(create_file_storage),
) -> AsyncGenerator[AsyncFileSession, None]:
    session = async_session()
    await session.recover()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
