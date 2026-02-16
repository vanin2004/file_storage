from functools import lru_cache
import os

from typing import AsyncGenerator, Callable

from fastapi import Depends

from src.services import AsyncFileSession

from src.settings import fs_config


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
