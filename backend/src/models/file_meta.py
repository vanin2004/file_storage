import datetime
from sqlalchemy import String, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .declarative_base import Base


class FileMeta(Base):
    """
    SQLAlchemy модель для таблицы метаданных файлов.
    Хранит информацию о файлах, но не само содержимое.
    uuid - уникальный идентификатор файла (UUID).
    filename - имя файла (без расширения).
    file_extension - расширение файла (например, "txt").
    size - размер файла в байтах.
    path - виртуальный путь.
    comment - произвольный комментарий к файлу.
    created_at - дата и время создания записи (UTC).
    updated_at - дата и время последнего обновления метаданных файла.

    установлено ограничение на уникальность комбинации path + filename + file_extension, чтобы предотвратить дублирование файлов с одинаковым полным путем.
    """

    __tablename__ = "file_meta"

    __table_args__ = (
        UniqueConstraint(
            "path", "filename", "file_extension", name="uq_file_full_path"
        ),
    )

    uuid: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, index=True)
    file_extension: Mapped[str] = mapped_column(String, index=True)
    size: Mapped[int] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(String, index=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
