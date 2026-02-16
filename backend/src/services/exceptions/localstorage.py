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
