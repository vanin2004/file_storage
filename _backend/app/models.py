import datetime
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class FileMeta(Base):
    """
    SQLAlchemy модель для таблицы метаданных файлов.
    Хранит информацию о файлах, но не само содержимое.
    """

    __tablename__ = "file_meta"

    uuid: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    """Уникальный идентификатор файла (UUID)."""

    filename: Mapped[str] = mapped_column(String, index=True)
    """Имя файла (без расширения)."""

    file_extension: Mapped[str] = mapped_column(String, index=True)
    """Расширение файла (например, ".txt")."""

    size: Mapped[int] = mapped_column(Integer)
    """Размер файла в байтах."""

    path: Mapped[str] = mapped_column(String, index=True)
    """Виртуальный путь или категория файла."""

    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    """Произвольный комментарий к файлу."""

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    """Дата и время создания файла (UTC)."""

    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    """Дата и время последнего обновления метаданных файла."""
