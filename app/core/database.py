from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from app.core.settings import settings
from app.exceptions.database import DatabaseError
import asyncio


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""

    pass


# Создание асинхронного движка базы данных
engine = create_async_engine(settings.database_url, echo=settings.debug)

# Фабрика сессий. expire_on_commit=False важно для асинхронной работы,
# чтобы объекты оставались доступными после коммита без нового запроса к БД.
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор сессий базы данных для использования в FastAPI зависимостях.
    Обеспечивает автоматический commit при успехе и rollback при ошибке.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise DatabaseError("Database transaction failed and was rolled back.")


async def create_database():
    """Создает все таблицы в базе данных при старте приложения."""
    retries = 5
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2)
            else:
                raise DatabaseError(
                    f"Error creating database after {retries} attempts: {e}"
                )
