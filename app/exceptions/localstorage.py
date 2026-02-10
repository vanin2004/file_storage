class LocalStorageError(Exception):
    """Base exception for local storage errors."""

    pass


class LocalStorageUnavailableError(LocalStorageError):
    """Raised when the local storage is unavailable (e.g., disk full, permission issues)."""

    pass


class FileLockError(LocalStorageError):
    """Raised when acquiring or releasing a file lock fails."""

    pass


class FileNotFoundError(LocalStorageError):
    """Raised when a requested file is not found in storage."""

    pass


class FileWriteError(LocalStorageError):
    """Raised when writing a file to storage fails."""

    pass
