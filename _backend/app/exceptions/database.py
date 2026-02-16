class DatabaseError(Exception):
    """Базовый класс для ошибок бд"""

    pass


class DatabaseConnectionError(DatabaseError):
    """Ошибка подключения к базе данных"""

    pass


class DatabaseOperationError(DatabaseError):
    """Ошибка выполнения операции с базой данных"""

    pass
