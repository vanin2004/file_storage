import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class FileMeta(Base):
    """
    SQLAlchemy модель для таблицы метаданных файлов.
    Хранит информацию о файлах, но не само содержимое.
    """

    __tablename__ = "file_meta"

    # Уникальный идентификатор файла (UUID)
    uuid: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    # Имя файла (без расширения)
    filename: Mapped[str] = mapped_column(String, index=True)

    # Расширение файла
    file_extension: Mapped[str] = mapped_column(String, index=True)

    # Виртуальный путь или категория файла
    path: Mapped[str] = mapped_column(String, index=True)

    # Произвольный комментарий
    comment: Mapped[str | None] = mapped_column(String, nullable=True)

    # Дата и время создания (UTC)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    # Дата и время последнего обновления
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # is_pending = Column(Boolean, default=True, nullable=False)
    # is_deleted = Column(Boolean, default=False, nullable=False)
