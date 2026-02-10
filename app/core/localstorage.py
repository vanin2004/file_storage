import os
import asyncio
import time
from enum import Enum
from typing import AsyncGenerator, IO

import aiofiles
import aiofiles.os
import portalocker

from app.core.settings import settings
from app.exceptions.localstorage import FileLockError, LocalStorageUnavailableError


class LockMode(str, Enum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


LOCK_FILE_SUFFIX = ".lock"


class AsyncFileSession:
    """
    Асинхронная сессия для работы с файловой системой с поддержкой транзакций и блокировок.
    Реализует паттерн Unit of Work для файловых операций.
    """

    def __init__(
        self,
        storage_path: str,
        pending_prefix: str = "pending_",
        lock_timeout: float = 10.0,
    ):
        self._storage_path = storage_path
        self._pending_prefix = pending_prefix
        self._lock_timeout = lock_timeout
        self._pending: dict[str, bytes] = {}
        # Хранит активные блокировки: имя файла -> (файловый дескриптор, режим блокировки)
        self._locks: dict[str, tuple[IO[str], LockMode]] = {}
        os.makedirs(storage_path, exist_ok=True)

    def _lock_path(self, file_name: str) -> str:
        """Возвращает путь к lock-файлу"""
        return os.path.join(self._storage_path, f"{file_name}{LOCK_FILE_SUFFIX}")

    async def _acquire_lock(self, file_name: str, mode: LockMode) -> None:
        """
        Захватывает блокировку (SHARED или EXCLUSIVE) на файл.
        Использует portalocker для OS-level блокировок.
        Если блокировка занята - ждет освобождения с таймаутом.
        """
        if file_name in self._locks:
            lock_file, current_mode = self._locks[file_name]
            if current_mode == LockMode.EXCLUSIVE or current_mode == mode:
                return
            await self._release_lock(file_name)

        lock_path = self._lock_path(file_name)

        def _lock() -> IO[str]:
            lock_file = open(lock_path, "a")
            lock_type = (
                portalocker.LOCK_SH if mode == LockMode.SHARED else portalocker.LOCK_EX
            )
            start_time = time.time()
            while time.time() - start_time < self._lock_timeout:
                try:
                    portalocker.lock(lock_file, lock_type | portalocker.LOCK_NB)
                    return lock_file
                except portalocker.LockException:
                    time.sleep(0.1)  # повтор каждые 100мс
            raise FileLockError(
                f"Could not acquire {mode} lock for {file_name} within timeout"
            )

        self._locks[file_name] = (await asyncio.to_thread(_lock), mode)

    async def _release_lock(self, file_name: str) -> None:
        """Освобождает блокировку файла"""
        entry = self._locks.pop(file_name, None)
        if entry is None:
            return

        lock_file, _ = entry

        def _unlock() -> None:
            portalocker.unlock(lock_file)
            lock_file.close()

        await asyncio.to_thread(_unlock)

    async def recover(self) -> None:
        """
        Восстановление после сбоя.
        Удаляет все 'повисшие' pending-файлы, которые не были закоммичены.
        """
        files = await aiofiles.os.listdir(self._storage_path)
        pending_files = [f for f in files if f.startswith(self._pending_prefix)]

        for pending_name in pending_files:
            file_name = pending_name[len(self._pending_prefix) :]
            await self._acquire_lock(file_name, LockMode.EXCLUSIVE)
            try:
                pending_path = os.path.join(self._storage_path, pending_name)
                await aiofiles.os.remove(pending_path)
            finally:
                await self._release_lock(file_name)

    async def add(self, file_bytes: bytes, file_name: str) -> None:
        """Добавляет файл в очередь на запись (в памяти)"""
        await self._acquire_lock(file_name, LockMode.EXCLUSIVE)
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
            for file_name in list(self._pending.keys()):
                await self._release_lock(file_name)
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
            for file_name in list(self._pending.keys()):
                await self._release_lock(file_name)
            self._pending.clear()

    async def get(self, file_name: str) -> bytes:
        await self._acquire_lock(file_name, LockMode.SHARED)
        try:
            async with aiofiles.open(
                os.path.join(self._storage_path, file_name), "rb"
            ) as in_file:
                return await in_file.read()
        finally:
            await self._release_lock(file_name)

    async def delete(self, file_name: str) -> bool:
        await self._acquire_lock(file_name, LockMode.EXCLUSIVE)
        try:
            file_path = os.path.join(self._storage_path, file_name)
            if await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                return True
            return False
        finally:
            await self._release_lock(file_name)

    async def list_files(self) -> list[str]:
        try:
            files = await aiofiles.os.listdir(self._storage_path)
            return [
                f
                for f in files
                if not f.startswith(self._pending_prefix) and not f.endswith(".lock")
            ]
        except Exception:
            raise LocalStorageUnavailableError("File storage is currently unavailable")

    async def list_all_files(self) -> list[str]:
        try:
            return await aiofiles.os.listdir(self._storage_path)
        except Exception:
            raise LocalStorageUnavailableError("File storage is currently unavailable")

    async def is_exists(self, file_name: str) -> bool:
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
