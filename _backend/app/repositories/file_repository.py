from app.core.localstorage import AsyncFileSession


class FileRepository:
    """
    Репозиторий для работы с файловым хранилищем.
    Абстрагирует работу с AsyncFileSession.
    """

    def __init__(self, session: AsyncFileSession):
        """
        Инициализация репозитория файлового хранилища.

        Args:
            session (AsyncFileSession): сессия файлового хранилища
        """
        self._session = session

    async def save(self, file_data: bytes, file_name: str) -> bool:
        """
        Сохраняет данные файла (добавляет в сессию).

        Args:
            file_data (bytes): содержимое файла
            file_name (str): имя файла
        Returns:
            bool: True если успешно
        """
        await self._session.add(file_data, file_name)
        await self._session.flush()
        return True

    async def get(self, file_name: str) -> bytes:
        """
        Получает содержимое файла.

        Args:
            file_name (str): имя файла для чтения
        Returns:
            bytes: содержимое файла
        """
        return await self._session.get(file_name)

    async def delete(self, file_name: str) -> bool:
        """
        Удаляет файл.

        Args:
            file_name (str): имя файла для удаления
        Returns:
            bool: True если успешно
        """
        return await self._session.delete(file_name)

    async def list_files(self) -> list[str]:
        """
        Список файлов (без временных).

        Returns:
            list[str]: список файлов
        """
        return await self._session.list_files()

    async def list_all_files(self) -> list[str]:
        """
        Полный список файлов (включая временные).

        Returns:
            list[str]: список всех файлов (включая временные)
        """
        return await self._session.list_all_files()

    async def is_exists(self, file_name: str) -> bool:
        """
        Проверка существования файла.

        Args:
            file_name (str): имя файла
        Returns:
            bool: True если файл существует
        """
        return await self._session.is_exists(file_name)

    async def delete_files_not_in_uuids(self, uuids: set[str]) -> None:
        """
        Удаляет файлы, которых нет в переданном множестве UUID.

        Args:
            uuids (set[str]): множество допустимых UUID файлов
        """
        files = await self._session.list_files()
        for file in files:
            if file not in uuids:
                await self.delete(file)
