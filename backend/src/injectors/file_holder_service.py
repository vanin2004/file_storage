from fastapi import Depends
from typing import AsyncGenerator

from src.services import FileHolderService
from .database import get_db
from .localstorage import get_fs


async def get_file_holder_service(
    file_session=Depends(get_fs), db_session=Depends(get_db)
) -> AsyncGenerator[FileHolderService, None]:
    """
    Зависимость Unit of Work, координирующая транзакции между БД и Файловой Системой.
    Гарантирует, что изменения в Файловой Системе будут зафиксированы только если успешна транзакция БД.
    """

    service = FileHolderService(
        file_session=file_session,
        file_meta_session=db_session,
    )

    try:
        yield service

        await db_session.commit()
        await file_session.commit()

    except Exception:
        await db_session.rollback()
        await file_session.rollback()
        raise
