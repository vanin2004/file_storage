from typing import Sequence
from app.repositories.file_repository import FileRepository
from app.repositories.file_meta_repository import FileMetaRepository
from app.schemas.file import FileCreate, FileUpdate
from app.models import FileMeta
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
        self._file_repository = file_repository
        self._file_meta_repository = file_meta_repository

    @staticmethod
    def _generate_file_path(file_id: uuid.UUID, file_extension: str) -> str:
        """Генерирует уникальное имя файла для хранения на диске (UUID.ext)"""
        return f"{file_id}"

    async def create_file(
        self,
        file_data: bytes,
        file_create: FileCreate,
    ) -> FileMeta:
        """
        Создает новый файл.
        Проверяет уникальность, сохраняет метаданные и содержимое.
        """

        if (
            await self._file_meta_repository.get_by_path_filename_extension(
                file_path=file_create.path,
                filename=file_create.filename,
                file_extension=file_create.file_extension,
            )
            is not None
        ):
            raise Exception(
                "File with the same path, filename and extension already exists"
            )

        file_id = uuid.uuid4()

        file_meta = await self._file_meta_repository.save(
            uuid=file_id,
            file_name=file_create.filename,
            file_extension=file_create.file_extension,
            file_path=file_create.path,
            comment=file_create.comment,
        )

        file_path = self._generate_file_path(file_id, file_create.file_extension)

        await self._file_repository.save(file_data, file_path)

        return file_meta

    async def get_file_meta(self, file_id: uuid.UUID) -> FileMeta | None:
        return await self._file_meta_repository.get_by_id(file_id)

    async def get_file_by_id(self, file_id: uuid.UUID) -> bytes:
        file_meta = await self.get_file_meta(file_id)
        if file_meta is None:
            raise Exception("File metadata not found")

        file_path = self._generate_file_path(
            uuid.UUID(file_meta.uuid), file_meta.file_extension
        )
        file_bytes = await self._file_repository.get(file_path)

        return file_bytes

    async def get_file_by_path_filename_extension(
        self, file_path: str, filename: str, file_extension: str
    ) -> bytes:
        file_meta = await self._file_meta_repository.get_by_path_filename_extension(
            file_path=file_path,
            filename=filename,
            file_extension=file_extension,
        )
        if file_meta is None:
            raise Exception("File metadata not found")

        file_path = self._generate_file_path(
            uuid.UUID(file_meta.uuid), file_meta.file_extension
        )
        file_bytes = await self._file_repository.get(file_path)

        return file_bytes

    async def delete_file(self, file_id: uuid.UUID) -> bool:
        file_meta = await self.get_file_meta(file_id)
        if file_meta is None:
            raise Exception("File metadata not found")

        file_path = self._generate_file_path(
            uuid.UUID(file_meta.uuid), file_meta.file_extension
        )

        await self._file_repository.delete(file_path)
        await self._file_meta_repository.delete(file_meta)

        return True

    async def list_files(self) -> Sequence[FileMeta]:
        return await self._file_meta_repository.list()

    async def update_file_meta(
        self, file_id: uuid.UUID, update: FileUpdate
    ) -> FileMeta:
        file_meta = await self.get_file_meta(file_id)
        if file_meta is None:
            raise Exception("File metadata not found")

        data = update.model_dump(exclude_unset=True)
        if not data:
            return file_meta

        return await self._file_meta_repository.update(file_meta, data)
