from typing import Sequence
from app.repositories.file_repository import FileRepository
from app.repositories.file_meta_repository import FileMetaRepository
from app.schemas import FileCreate, FileUpdate
from app.models import FileMeta
from app.exceptions.service import (
    ServiceFileAlreadyExistsError,
    ServiceFileNotFoundError,
)
import uuid


class FileHolderService:
    """
    Сервис бизнес-логики для управления файлами.
    Оркестрирует работу с метаданными (БД) и физическим хранилищем файлов.
    """

    def __init__(
        self,
        file_repository: FileRepository,
        file_meta_repository: FileMetaRepository,
    ):
        """
        Инициализация сервиса управления файлами.

        Args:
            file_repository (FileRepository): репозиторий работы с файлами
            file_meta_repository (FileMetaRepository): репозиторий метаданных
        """
        self._file_repository = file_repository
        self._file_meta_repository = file_meta_repository

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
        file_create: FileCreate,
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

        if (
            await self._file_meta_repository.get_by_path_filename_extension(
                file_path=file_create.path,
                filename=file_create.filename,
                file_extension=file_create.file_extension,
            )
            is not None
        ):
            raise ServiceFileAlreadyExistsError(
                "File with the same path, filename and extension already exists"
            )

        file_id = uuid.uuid4()

        file_meta = await self._file_meta_repository.save(
            uuid=file_id,
            file_name=file_create.filename,
            file_extension=file_create.file_extension,
            file_path=file_create.path,
            size=file_create.size,
            comment=file_create.comment,
        )

        file_path = self._generate_file_path(file_id)

        await self._file_repository.save(file_data, file_path)

        return file_meta

    async def get_file_meta(self, file_id: uuid.UUID) -> FileMeta:
        """
        Получает метаданные файла по ID.

        Args:
            file_id (uuid.UUID): идентификатор файла
        Returns:
            FileMeta: найденная запись
        """

        file_meta = await self._file_meta_repository.get_by_id(file_id)
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
            file_bytes = await self._file_repository.get(file_path)
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
        file_meta = await self._file_meta_repository.get_by_path_filename_extension(
            file_path=file_path,
            filename=filename,
            file_extension=file_extension,
        )
        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")

        file_path = self._generate_file_path(uuid.UUID(file_meta.uuid))
        file_bytes = await self._file_repository.get(file_path)

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

        await self._file_repository.delete(file_path)
        await self._file_meta_repository.delete(file_meta)

        return True

    async def list_files(self) -> Sequence[FileMeta]:
        return await self._file_meta_repository.list()

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

        return await self._file_meta_repository.get_by_path_startswith(path_prefix)

    async def update_file_meta(
        self,
        file_id: uuid.UUID,
        update: FileUpdate,
    ) -> FileMeta:
        """
        Обновляет метаданные файла.

        Args:
            file_id (uuid.UUID): идентификатор файла
            update (FileUpdate): данные для обновления
        Returns:
            FileMeta: обновленная запись
        """
        file_meta = await self.get_file_meta(file_id)
        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")

        data = update.model_dump(exclude_unset=True)
        if not data:
            return file_meta

        return await self._file_meta_repository.update(file_meta, data)

    async def sync_storage_with_db(self) -> None:
        """
        Синхронизирует физическое хранилище с базой данных.
        Удаляет файлы, которые есть в хранилище, но отсутствуют в БД.
        И удаляет метаданные файлов, которых нет в хранилище.
        """
        uuids = {
            file_meta.uuid for file_meta in await self._file_meta_repository.list()
        }
        await self._file_repository.delete_files_not_in_uuids(uuids)

    async def get_file_meta_by_full_path(self, file_path: str) -> FileMeta:
        """
        Получает метаданные файла по полному пути.

        Args:
            file_path (str): полный путь к файлу
        Returns:
            FileMeta: найденная запись
        """
        file_meta = await self._file_meta_repository.get_by_full_path(file_path)
        if file_meta is None:
            raise ServiceFileNotFoundError("File metadata not found")
        return file_meta
