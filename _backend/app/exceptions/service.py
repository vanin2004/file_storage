class ServiceError(Exception):
    """Базовый класс для ошибок сервисного слоя"""

    pass


class ServiceFileNotFoundError(ServiceError):
    """Ошибка: файл не найден"""

    pass


class ServiceFileAlreadyExistsError(ServiceError):
    """Ошибка: файл уже существует"""

    pass
