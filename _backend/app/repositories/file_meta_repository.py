from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, case
from sqlalchemy.exc import SQLAlchemyError
from typing import Sequence
import datetime

from uuid import UUID
from app.models import FileMeta
from app.exceptions.database import DatabaseOperationError


class FileMetaRepository:
    """
    Репозиторий для работы с метаданными файлов в БД.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория метаданных файлов.

        Args:
            session (AsyncSession): асинхронная сессия БД
        """
        self._session = session

    @staticmethod
    def _apply_pagination(stmt, limit: int | None, offset: int):
        """
        Применяет пагинацию к SQL-запросу.

        Args:
            stmt: SQL запрос
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            stmt: SQL запрос с применённой пагинацией
        """
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
        size: int,
        comment: str | None = None,
    ) -> FileMeta:
        """
        Сохраняет новую запись о файле.

        Args:
            uuid (UUID): Уникальный идентификатор файла
            file_name (str): Имя файла без расширения
            file_extension (str): Расширение файла
            file_path (str): Путь расположения файла
            size (int): Размер файла в байтах
            comment (str | None): Комментарий к файлу
        Returns:
            FileMeta: Сохранённая запись о файле
        """
        created_at = datetime.datetime.now(datetime.timezone.utc)
        file_meta = FileMeta(
            uuid=str(uuid),
            filename=file_name,
            file_extension=file_extension,
            path=file_path,
            size=size,
            comment=comment,
            created_at=created_at,
            updated_at=None,
        )
        try:
            self._session.add(file_meta)
            await self._session.flush()
            return file_meta
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error saving file metadata: {e}")

    async def get_by_id(
        self, file_id: UUID | str, limit: int | None = 1, offset: int = 0
    ) -> FileMeta | None:
        """
        Поиск метаданных файла по UUID.

        Args:
            file_id (UUID | str): UUID файла
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            FileMeta | None: Найденная запись или None
        """
        try:
            stmt = select(FileMeta).where(FileMeta.uuid == str(file_id))
            stmt = self._apply_pagination(stmt, limit, offset)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error retrieving file metadata by ID: {e}")

    async def get_by_path_filename_extension(
        self,
        file_path: str,
        filename: str,
        file_extension: str,
        limit: int | None = 1,
        offset: int = 0,
    ) -> FileMeta | None:
        """
        Получить метаданные по пути, имени и расширению файла.

        Args:
            file_path (str): Путь к файлу
            filename (str): Имя файла
            file_extension (str): Расширение файла
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            FileMeta | None: Найденная запись или None
        """
        try:
            stmt = select(FileMeta).where(
                FileMeta.path == file_path,
                FileMeta.filename == filename,
                FileMeta.file_extension == file_extension,
            )
            stmt = self._apply_pagination(stmt, limit, offset)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationError(
                f"Error retrieving file metadata by path info: {e}"
            )

    async def get_by_path(
        self, file_path: str, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        """
        Получить список файлов по пути.

        Args:
            file_path (str): Путь к файлу
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            Sequence[FileMeta]: Список найденных файлов
        """
        try:
            stmt = select(FileMeta).where(FileMeta.path == file_path)
            stmt = self._apply_pagination(stmt, limit, offset)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error retrieving files by path: {e}")

    async def get_by_word_in_path(
        self, word: str, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        """
        Получить список файлов, путь которых содержит слово.

        Args:
            word (str): Слово для поиска в пути
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            Sequence[FileMeta]: Список найденных файлов
        """
        try:
            stmt = select(FileMeta).where(FileMeta.path.contains(word))
            stmt = self._apply_pagination(stmt, limit, offset)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error retrieving files by word in path: {e}")

    async def get_by_path_startswith(
        self, word: str, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        """
        Получить список файлов, путь которых начинается с заданного слова.

        Args:
            word (str): Начало пути
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            Sequence[FileMeta]: Список найденных файлов
        """
        try:
            stmt = select(FileMeta).where(FileMeta.path.startswith(word))
            stmt = self._apply_pagination(stmt, limit, offset)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseOperationError(
                f"Error retrieving files by path startswith: {e}"
            )

    async def list(
        self, limit: int | None = None, offset: int = 0
    ) -> Sequence[FileMeta]:
        """
        Получить список всех файлов с пагинацией.

        Args:
            limit (int | None): максимум записей
            offset (int): смещение
        Returns:
            Sequence[FileMeta]: Список файлов
        """
        try:
            stmt = self._apply_pagination(select(FileMeta), limit, offset)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error listing files: {e}")

    async def delete(self, file_meta: FileMeta) -> bool:
        """
        Удалить одну запись о файле.

        Args:
            file_meta (FileMeta): Модель метаданных файла
        Returns:
            bool: True если удалено успешно
        """
        try:
            await self._session.delete(file_meta)
            return True
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error deleting file metadata: {e}")

    async def delete_many(self, file_metas: Sequence[FileMeta]) -> bool:
        """
        Удалить несколько записей о файлах.

        Args:
            file_metas (Sequence[FileMeta]): Список моделей метаданных файлов
        Returns:
            bool: True если хотя бы одна запись удалена
        """
        if not file_metas:
            return False

        uuids = [str(file_meta.uuid) for file_meta in file_metas]
        try:
            result = await self._session.execute(
                delete(FileMeta)
                .where(FileMeta.uuid.in_(uuids))
                .returning(FileMeta.uuid)
            )
            return result.first() is not None
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error deleting multiple file metadata: {e}")

    async def update(self, file_meta: FileMeta, data: dict) -> FileMeta:
        """
        Обновить запись о файле.

        Args:
            file_meta (FileMeta): Модель метаданных файла
            data (dict): Данные для обновления
        Returns:
            FileMeta: Обновлённая запись
        """
        try:
            for key, value in data.items():
                setattr(file_meta, key, value)
            file_meta.updated_at = datetime.datetime.now(datetime.timezone.utc)
            await self._session.flush()
            return file_meta
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error updating file metadata: {e}")

    async def get_by_full_path(self, full_path: str) -> FileMeta | None:
        """
        Получает метаданные файла по полному пути.

        Args:
            full_path (str): Полный путь к файлу (включая имя и расширение)
        Returns:
            FileMeta | None: Найденная запись или None
        """
        try:
            stmt = select(FileMeta).where(
                func.concat(
                    FileMeta.path,
                    FileMeta.filename,
                    case(
                        (FileMeta.file_extension != "", "." + FileMeta.file_extension),
                        else_="",
                    ),
                )
                == full_path
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Error retrieving file by full path: {e}")
