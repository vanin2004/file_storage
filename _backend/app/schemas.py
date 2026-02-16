"""
Определение типов с валидацией.
Filename: 1-255 символов, буквы/цифры/._-.
FileExtension: 0-10 символов, буквы и цифры.
FilePath: 1-1024 символов, начинается и заканчивается на "/".
"""

from uuid import UUID
from typing import Annotated
from pydantic import BaseModel, Field

Filename = Annotated[
    str, Field(min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9._-]+$")
]
FileExtension = Annotated[
    str, Field(min_length=0, max_length=10, pattern=r"^[a-zA-Z0-9]+$")
]
FilePath = Annotated[
    str, Field(min_length=1, max_length=1024, pattern=r"^/[a-zA-Z0-9._/-]+/$")
]


class FileCreate(BaseModel):
    """Модель для создания записи о файле"""

    filename: Filename
    file_extension: FileExtension
    path: FilePath
    size: int
    comment: str | None = None


class FileRead(BaseModel):
    """Модель для чтения записи о файле (возвращается клиенту)"""

    id: UUID
    filename: str
    file_extension: str
    path: str
    size: int
    created_at: str
    updated_at: str | None = None
    comment: str | None = None


class FileUpdate(BaseModel):
    """Модель для обновления метаданных файла"""

    filename: Filename | None = None
    path: FilePath | None = None
    comment: str | None = None
