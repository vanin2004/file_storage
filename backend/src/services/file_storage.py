import aiofiles
import aiofiles.os
import os


class LocalStorageError(Exception):
    """Базовый класс для ошибок локального хранилища."""

    pass


class LocalStorageUnavailableError(LocalStorageError):
    """Вызывается, когда локальное хранилище недоступно (например, диск полон, проблемы с правами)."""

    pass


class FileNotFoundError(LocalStorageError):
    """Вызывается, когда запрашиваемый файл не найден в хранилище."""

    pass


class FileWriteError(LocalStorageError):
    """Вызывается, когда запись файла в хранилище не удается."""

    pass


class AsyncFileSession:
    """
    Асинхронная сессия для работы с файловой системой с поддержкой транзакций и блокировок.
    Реализует паттерн Unit of Work для файловых операций.
    """

    def __init__(
        self,
        storage_path: str,
        pending_prefix: str = "pending_",
    ):
        """
        Инициализация асинхронной файловой сессии.

        Args:
            storage_path (str): путь к директории хранения файлов
            pending_prefix (str): префикс для временных файлов
        """
        self._storage_path = storage_path
        self._pending_prefix = pending_prefix
        self._pending: dict[str, bytes] = {}
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
            try:
                async with aiofiles.open(pending_path, "wb") as out_file:
                    await out_file.write(file_bytes)
            except Exception:
                raise FileWriteError(f"Failed to write pending file: {pending_name}")

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
        except Exception as e:
            raise FileWriteError(f"Failed to commit files: {e}")
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
        except Exception as e:
            raise FileWriteError(f"Failed to rollback files: {e}")
        finally:
            self._pending.clear()

    async def get(self, file_name: str) -> bytes:
        """
        Читает содержимое файла.

        Args:
            file_name (str): имя файла для чтения
        Returns:
            bytes: содержимое файла
        """
        try:
            async with aiofiles.open(
                os.path.join(self._storage_path, file_name), "rb"
            ) as in_file:
                return await in_file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{file_name}' not found in storage")

    async def delete(self, file_name: str) -> bool:
        """
        Удаляет файл из хранилища.

        Args:
            file_name (str): имя файла для удаления
        Returns:
            bool: True если файл удалён
        """
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
