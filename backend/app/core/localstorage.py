import os

from typing import AsyncGenerator

import aiofiles
import aiofiles.os

from app.core.settings import settings
from app.exceptions.localstorage import LocalStorageUnavailableError


class AsyncFileSession:
    """
    Асинхронная сессия для работы с файловой системой с поддержкой транзакций и блокировок.
    Реализует паттерн Unit of Work для файловых операций.
    """

    def __init__(
        self,
        storage_path: str,  # Путь к директории хранения файлов
        pending_prefix: str = "pending_",  # Префикс для временных файлов
    ):
        self._storage_path = storage_path
        self._pending_prefix = pending_prefix
        self._pending: dict[str, bytes] = {}  # Буфер для ожидающих записи файлов
        os.makedirs(storage_path, exist_ok=True)

    async def recover(self) -> None:
        """
        Восстановление после сбоя.
        Удаляет все 'повисшие' pending-файлы, которые не были закоммичены.
        """
        files = await aiofiles.os.listdir(self._storage_path)
        pending_files = [f for f in files if f.startswith(self._pending_prefix)]

        for pending_name in pending_files:
            pending_path = os.path.join(self._storage_path, pending_name)
            await aiofiles.os.remove(pending_path)

    async def add(self, file_bytes: bytes, file_name: str) -> None:
        """Добавляет файл в очередь на запись (в памяти)"""
        self._pending[file_name] = file_bytes

    async def flush(self) -> None:
        """Сбрасывает pending изменения на диск во временные файлы"""
        for file_name, file_bytes in self._pending.items():
            pending_name = f"{self._pending_prefix}{file_name}"
            pending_path = os.path.join(self._storage_path, pending_name)
            async with aiofiles.open(pending_path, "wb") as out_file:
                await out_file.write(file_bytes)

    async def commit(self) -> None:
        """
        Фиксация транзакции.
        1. Записываем данные во временные файлы (если еще не записаны).
        2. Атомарно переименовываем временные файлы в основные.
        """
        try:
            for file_name in list(self._pending.keys()):
                pending_name = f"{self._pending_prefix}{file_name}"
                pending_path = os.path.join(self._storage_path, pending_name)
                final_path = os.path.join(self._storage_path, file_name)

                # Сначала запишем данные из памяти во временный файл
                if file_name in self._pending:
                    async with aiofiles.open(pending_path, "wb") as out_file:
                        await out_file.write(self._pending[file_name])

                if await aiofiles.os.path.exists(final_path):
                    await aiofiles.os.remove(final_path)

                if await aiofiles.os.path.exists(pending_path):
                    await aiofiles.os.rename(pending_path, final_path)
        finally:
            self._pending.clear()

    async def rollback(self) -> None:
        """
        Откат транзакции.
        Удаляет временные файлы.
        """
        try:
            for file_name in list(self._pending.keys()):
                pending_name = f"{self._pending_prefix}{file_name}"
                pending_path = os.path.join(self._storage_path, pending_name)
                if await aiofiles.os.path.exists(pending_path):
                    await aiofiles.os.remove(pending_path)
        finally:
            self._pending.clear()

    async def get(self, file_name: str) -> bytes:  # file_name: имя файла для чтения
        """Читает содержимое файла"""
        async with aiofiles.open(
            os.path.join(self._storage_path, file_name), "rb"
        ) as in_file:
            return await in_file.read()

    async def delete(self, file_name: str) -> bool:  # file_name: имя файла для удаления
        """Удаляет файл из хранилища"""
        file_path = os.path.join(self._storage_path, file_name)
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
            return True
        return False

    async def list_files(self) -> list[str]:
        try:
            files = await aiofiles.os.listdir(self._storage_path)
        except Exception:
            raise LocalStorageUnavailableError("File storage is currently unavailable")
        return [f for f in files if not f.startswith(self._pending_prefix)]

    async def list_all_files(self) -> list[str]:
        try:
            return await aiofiles.os.listdir(self._storage_path)
        except Exception:
            raise LocalStorageUnavailableError("File storage is currently unavailable")

    async def is_exists(self, file_name: str) -> bool:
        """Проверяет существование файла"""
        try:
            return await aiofiles.os.path.exists(
                os.path.join(self._storage_path, file_name)
            )
        except Exception:
            raise LocalStorageUnavailableError("File storage is currently unavailable")


async def get_file_session() -> AsyncGenerator[AsyncFileSession, None]:
    session = AsyncFileSession(
        storage_path=settings.file_storage_path,
        pending_prefix=settings.pending_file_prefix,
    )
    await session.recover()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise


def create_file_storage_directory():
    os.makedirs(settings.file_storage_path, exist_ok=True)
