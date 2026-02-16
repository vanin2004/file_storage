from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session
from app.core.localstorage import AsyncFileSession, get_file_session
from app.core.settings import settings
from app.repositories.file_repository import FileRepository
from app.repositories.file_meta_repository import FileMetaRepository
from app.services.file_holder_service import FileHolderService


def get_file_repository(
    session: AsyncFileSession = Depends(get_file_session),
) -> FileRepository:
    return FileRepository(session)


def get_file_meta_repository(
    db: AsyncSession = Depends(get_db),
) -> FileMetaRepository:
    return FileMetaRepository(db)


async def get_file_holder_service() -> AsyncGenerator[FileHolderService, None]:
    """
    Зависимость Unit of Work, координирующая транзакции между БД и Файловой Системой.
    Гарантирует, что изменения в Файловой Системе будут зафиксированы только если успешна транзакция БД.
    """
    file_session = AsyncFileSession(
        storage_path=settings.file_storage_path,
        pending_prefix=settings.pending_file_prefix,
    )
    await file_session.recover()

    async with async_session() as db_session:
        file_repo = FileRepository(file_session)
        meta_repo = FileMetaRepository(db_session)

        service = FileHolderService(
            file_repository=file_repo,
            file_meta_repository=meta_repo,
        )

        try:
            yield service

            await db_session.commit()
            await file_session.commit()

        except Exception:
            await db_session.rollback()
            await file_session.rollback()
            raise
