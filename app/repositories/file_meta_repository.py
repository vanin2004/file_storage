from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Sequence
import datetime

from uuid import UUID
from app.models import FileMeta


class FileMetaRepository:
    """
    Репозиторий для работы с метаданными файлов в БД.
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _apply_pagination(stmt, limit: int | None, offset: int):
        """Применяет пагинацию к запросу"""
        stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return stmt

    async def save(
        self,
        uuid: UUID,
        file_name: str,
        file_extension: str,
        file_path: str,
        comment: str | None = None,
    ) -> FileMeta:
        """Сохраняет новую запись о файле"""

        created_at = datetime.datetime.now(datetime.timezone.utc)

        file_meta = FileMeta(
            uuid=str(uuid),
            filename=file_name,
            file_extension=file_extension,
            path=file_path,
            comment=comment,
            created_at=created_at,
            updated_at=None,
        )

        self._session.add(file_meta)
        await self._session.flush()

        return file_meta

    async def get_by_id(
        self, file_id: UUID | str, limit: int | None = 1, offset: int = 0
    ) -> FileMeta | None:
        """Поиск по UUID"""
        stmt = select(FileMeta).where(FileMeta.uuid == str(file_id))
        stmt = self._apply_pagination(stmt, limit, offset)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_path_filename_extension(
        self,
        file_path: str,
        filename: str,
        file_extension: str,
        limit: int | None = 1,
        offset: int = 0,
    ) -> FileMeta | None:
        stmt = select(FileMeta).where(
            FileMeta.path == file_path,
            FileMeta.filename == filename,
            FileMeta.file_extension == file_extension,
        )
        stmt = self._apply_pagination(stmt, limit, offset)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_path(
        self, file_path: str, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        stmt = select(FileMeta).where(FileMeta.path == file_path)
        stmt = self._apply_pagination(stmt, limit, offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_word_in_path(
        self, word: str, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        stmt = select(FileMeta).where(FileMeta.path.contains(word))
        stmt = self._apply_pagination(stmt, limit, offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_path_startswith(
        self, word: str, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        stmt = select(FileMeta).where(FileMeta.path.startswith(word))
        stmt = self._apply_pagination(stmt, limit, offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list(
        self, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        stmt = self._apply_pagination(select(FileMeta), limit, offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, file_meta: FileMeta) -> bool:
        await self._session.delete(file_meta)
        return True

    async def delete_many(self, file_metas: Sequence[FileMeta]) -> bool:
        if not file_metas:
            return False

        uuids = [str(file_meta.uuid) for file_meta in file_metas]
        result = await self._session.execute(
            delete(FileMeta).where(FileMeta.uuid.in_(uuids)).returning(FileMeta.uuid)
        )
        return result.first() is not None

    async def update(self, file_meta: FileMeta, data: dict) -> FileMeta:
        for key, value in data.items():
            setattr(file_meta, key, value)
        file_meta.updated_at = datetime.datetime.now(datetime.timezone.utc)
        await self._session.flush()
        return file_meta
