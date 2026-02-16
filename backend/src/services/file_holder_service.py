from typing import Sequence

from src.models.file_meta import FileMeta

from .file_storage import AsyncFileSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import uuid
from datetime import datetime, timezone


class ServiceError(Exception):
    """Базовый класс для ошибок сервисного слоя"""

    pass


class ServiceFileNotFoundError(ServiceError):
    """Ошибка: файл не найден"""

    pass


class ServiceFileAlreadyExistsError(ServiceError):
    """Ошибка: файл уже существует"""

    pass


class FileHolderService:
    """
    Сервис бизнес-логики для управления файлами.
    Оркестрирует работу с метаданными (БД) и физическим хранилищем файлов.
    """

    def __init__(self, file_session: AsyncFileSession, file_meta_session: AsyncSession):
        """
        Инициализация сервиса управления файлами.

        Args:
            file_session (AsyncFileSession): сессия работы с физическим хранилищем файлов
            file_meta_session (AsyncSession): сессия работы с метаданными файлов
        """
        self._file_session = file_session
        self._file_meta_session = file_meta_session

    @staticmethod
    def _generate_file_path(file_id: uuid.UUID) -> str:
        """
        Генерирует уникальное имя файла для хранения на диске (UUID).

        Args:
            file_id (uuid.UUID): идентификатор файла
        Returns:
            str: имя файла для хранения
        """
        return f"{file_id}"

    async def create_file(
        self,
        file_data: bytes,
        file_name: str,
        file_extension: str,
        file_path: str,
        comment: str | None = None,
    ) -> FileMeta:
        """
        Создает новый файл.
        Проверяет уникальность, сохраняет метаданные и содержимое.

        Args:
            file_data (bytes): содержимое файла
            file_create (FileCreate): метаданные для создания
        Returns:
            FileMeta: созданная запись
        """

        file_id = uuid.uuid4()

        file_meta = FileMeta(
            uuid=str(file_id),
            filename=file_name,
            file_extension=file_extension,
            path=file_path,
            size=len(file_data),
            comment=comment,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        self._file_meta_session.add(file_meta)
        try:
            await self._file_meta_session.flush()
        except IntegrityError as e:
            raise ServiceFileAlreadyExistsError(
                f"File with path '{file_path}', name '{file_name}' and extension '{file_extension}' already exists."
            ) from e
        except SQLAlchemyError as e:
            raise ServiceError(f"Failed to save file metadata: {e}") from e

        file_path = self._generate_file_path(file_id)

        await self._file_session.add(file_data, file_path)

        try:
            await self._file_session.flush()
        except Exception:
            await self._file_meta_session.rollback()
            raise ServiceError("Failed to save file content")

        return file_meta

    async def get_file_meta(self, file_id: uuid.UUID) -> FileMeta:
        """
        Получает метаданные файла по ID.

        Args:
            file_id (uuid.UUID): идентификатор файла
        Returns:
            FileMeta: найденная запись
        """

        file_meta = await self._file_meta_session.get(FileMeta, str(file_id))
        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")

        return file_meta

    async def get_file_by_id(self, file_id: uuid.UUID) -> bytes:
        """
        Получает содержимое файла по ID.

        Args:
            file_id (uuid.UUID): идентификатор файла
        Returns:
            bytes: содержимое файла
        """
        file_meta = await self.get_file_meta(file_id)

        file_path = self._generate_file_path(uuid.UUID(file_meta.uuid))
        try:
            file_bytes = await self._file_session.get(file_path)
        except FileNotFoundError:
            raise ServiceFileNotFoundError("File not found in storage")

        return file_bytes

    async def get_file_by_path_filename_extension(
        self,
        file_path: str,
        filename: str,
        file_extension: str,
    ) -> bytes:
        """
        Получает содержимое файла по полному пути, имени и расширению.

        Args:
            file_path (str): путь к файлу
            filename (str): имя файла
            file_extension (str): расширение файла
        Returns:
            bytes: содержимое файла
        """
        res = await self._file_meta_session.execute(
            select(FileMeta)
            .where(
                FileMeta.path == file_path,
                FileMeta.filename == filename,
                FileMeta.file_extension == file_extension,
            )
            .limit(1)
        )
        file_meta = res.scalar_one_or_none()

        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")

        file_path = self._generate_file_path(uuid.UUID(file_meta.uuid))
        file_bytes = await self._file_session.get(file_path)
        return file_bytes

    async def delete_file(self, file_id: uuid.UUID) -> bool:
        """
        Удаляет файл и его метаданные.

        Args:
            file_id (uuid.UUID): идентификатор файла для удаления
        Returns:
            bool: True если удалено
        """
        file_meta = await self.get_file_meta(file_id)

        file_path = self._generate_file_path(uuid.UUID(file_meta.uuid))

        await self._file_session.delete(file_path)
        await self._file_meta_session.delete(file_meta)

        return True

    async def list_files(self) -> Sequence[FileMeta]:
        file_meta_list = await self._file_meta_session.execute(select(FileMeta))
        return file_meta_list.scalars().all()

    async def search_files_by_path(self, path_prefix: str) -> Sequence[FileMeta]:
        """
        Ищет файлы по префиксу пути.

        Args:
            path_prefix (str): префикс пути для поиска
        Returns:
            Sequence[FileMeta]: найденные файлы
        """

        if len(path_prefix) == 0:
            return []
        if path_prefix[-1] != "/":
            path_prefix += "/"

        res = await self._file_meta_session.execute(
            select(FileMeta).where(FileMeta.path.startswith(path_prefix))
        )

        return res.scalars().all()

    async def update_file_meta(
        self,
        file_id: uuid.UUID,
        filename: str | None = None,
        file_extension: str | None = None,
        path: str | None = None,
        comment: str | None = None,
    ) -> FileMeta:
        """
        Обновляет метаданные файла.

        Args:
            file_id (uuid.UUID): идентификатор файла
            filename (str | None): новое имя файла
            file_extension (str | None): новое расширение файла
            path (str | None): новый путь к файлу
            comment (str | None): новый комментарий к файлу
        Returns:
            FileMeta: обновленная запись
        """
        if (
            filename is None
            and file_extension is None
            and path is None
            and comment is None
        ):
            raise ServiceError("No data provided for update")

        file_meta = await self.get_file_meta(file_id)
        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")

        file_meta.filename = filename or file_meta.filename
        file_meta.file_extension = file_extension or file_meta.file_extension
        file_meta.path = path or file_meta.path
        file_meta.comment = comment if comment is not None else file_meta.comment
        file_meta.updated_at = datetime.now(timezone.utc)

        try:
            await self._file_meta_session.flush()
        except SQLAlchemyError as e:
            raise ServiceError(f"Failed to update file metadata: {e}")

        return file_meta

    async def sync_storage_with_db(self) -> None:
        """
        Синхронизирует физическое хранилище с базой данных.
        Удаляет файлы, которые есть в хранилище, но отсутствуют в БД.
        И удаляет метаданные файлов, которых нет в хранилище.
        """
        res = await self._file_meta_session.execute(select(FileMeta))
        file_meta_list = res.scalars().all()

        uuids = {file_meta.uuid for file_meta in file_meta_list}
        files = await self._file_session.list_all_files()
        for file in files:
            if file not in uuids:
                try:
                    await self._file_session.delete(file)
                except FileNotFoundError:
                    pass
                except Exception as e:
                    raise ServiceError(f"Failed to delete file '{file}': {e}")

    async def get_file_meta_by_full_path(
        self, file_path: str, filename: str, file_extension: str
    ) -> FileMeta:
        """
        Получает метаданные файла по полному пути.

        Args:
            file_path (str): полный путь к файлу
            filename (str): имя файла
            file_extension (str): расширение файла
        Returns:
            FileMeta: найденная запись
        """
        res = await self._file_meta_session.execute(
            select(FileMeta).where(
                FileMeta.path == file_path,
                FileMeta.filename == filename,
                FileMeta.file_extension == file_extension,
            )
        )

        file_meta = res.scalar_one_or_none()
        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")
        return file_meta
