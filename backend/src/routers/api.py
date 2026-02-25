from uuid import UUID

from fastapi import Depends, File, Form, Query, Response, UploadFile
from fastapi.routing import APIRouter
from src.injectors import get_file_holder_service
from src.models import FileExtension, Filename, FilePath, FileRead, FileUpdate
from src.services import FileHolderService

router = APIRouter(prefix="/api")


def _to_file_meta_read(meta) -> FileRead:
    return FileRead.model_validate(meta)


@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "ok"}


@router.post("/files")
async def post_file(
    filename: Filename = Form(...),
    file_extension: FileExtension = Form(...),
    path: FilePath = Form(...),
    comment: str | None = Form(None),
    file: UploadFile = File(...),
    service: FileHolderService = Depends(get_file_holder_service),
) -> FileRead:
    """
    Загрузка нового файла.

    Args:
        filename (Filename): имя файла без расширения
        file_extension (FileExtension): расширение файла
        path (FilePath): путь расположения файла
        comment (str | None): опциональный комментарий
        file (UploadFile): загружаемый файл
        service (FileHolderService): сервис работы с файлами
    """

    file_data = await file.read()

    saved_meta = await service.create_file(
        file_data=file_data,
        file_name=filename,
        file_extension=file_extension,
        file_path=path,
        comment=comment,
    )
    return _to_file_meta_read(saved_meta)


@router.get("/files")
async def list_files(
    service: FileHolderService = Depends(get_file_holder_service),
) -> list[FileRead]:
    """Получение списка всех файлов"""
    files_meta = await service.list_files()
    return [_to_file_meta_read(meta) for meta in files_meta]


@router.get("/files/search")
async def search_files(
    file_path: FilePath = Query(...),
    service: FileHolderService = Depends(get_file_holder_service),
) -> list[FileRead]:
    """
    Поиск файлов по префиксу пути.

    Args:
        file_path (FilePath): префикс пути
        service (FileHolderService): сервис работы с файлами
    """
    files_meta = await service.search_files_by_path(file_path)
    return [_to_file_meta_read(meta) for meta in files_meta]


@router.get("/files/{file_id}/meta")
async def get_file_meta(
    file_id: UUID,
    service: FileHolderService = Depends(get_file_holder_service),
) -> FileRead:
    """
    Получение метаданных файла по ID.

    Args:
        file_id (UUID): идентификатор файла
        service (FileHolderService): сервис работы с файлами
    """
    meta = await service.get_file_meta(file_id)

    return _to_file_meta_read(meta)


@router.get("/files/{file_id}")
async def get_file(
    file_id: UUID,
    service: FileHolderService = Depends(get_file_holder_service),
) -> Response:
    """
    Получение содержимого файла по ID.

    Args:
        file_id (UUID): идентификатор файла
        service (FileHolderService): сервис работы с файлами
    """
    file_bytes = await service.get_file_by_id(file_id)
    return Response(content=file_bytes, media_type="application/octet-stream")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: UUID,
    service: FileHolderService = Depends(get_file_holder_service),
):
    """
    Удаление файла и метаданных по ID.

    Args:
        file_id (UUID): идентификатор файла
        service (FileHolderService): сервис работы с файлами
    """
    await service.delete_file(file_id)
    return {"status": "deleted", "file_id": str(file_id)}


@router.put("/files/{file_id}")
async def put_file(
    file_id: UUID,
    update: FileUpdate,
    service: FileHolderService = Depends(get_file_holder_service),
) -> FileRead:
    """
    Полная замена метаданных файла.

    Args:
        file_id (UUID): идентификатор файла
        update (FileUpdate): новые метаданные
        service (FileHolderService): сервис работы с файлами
    """
    updated = await service.update_file_meta(
        file_id=file_id,
        filename=update.filename,
        file_extension=update.file_extension,
        path=update.path,
        comment=update.comment,
    )
    return _to_file_meta_read(updated)


@router.patch("/files/{file_id}")
async def patch_file(
    file_id: UUID,
    update: FileUpdate,
    service: FileHolderService = Depends(get_file_holder_service),
) -> FileRead:
    """
    Частичное обновление метаданных файла.

    Args:
        file_id (UUID): идентификатор файла
        update (FileUpdate): новые метаданные
        service (FileHolderService): сервис работы с файлами
    """
    updated = await service.update_file_meta(
        file_id=file_id,
        filename=update.filename,
        file_extension=update.file_extension,
        path=update.path,
        comment=update.comment,
    )
    return _to_file_meta_read(updated)


@router.post("/files/synchronise")
async def synchronise_files(
    service: FileHolderService = Depends(get_file_holder_service),
):
    await service.sync_storage_with_db()
    return {"status": "synchronised"}


@router.get("/files/meta/by-path")
async def get_file_meta_by_full_path(
    path: str = Query(...),
    filename: str = Query(...),
    file_extension: str = Query(...),
    service: FileHolderService = Depends(get_file_holder_service),
) -> FileRead:
    """
    Получение метаданных файла по полному пути.

    Args:
        path (str): путь к файлу
        filename (str): имя файла
        file_extension (str): расширение файла
        service (FileHolderService): сервис работы с файлами
    """
    meta = await service.get_file_meta_by_full_path(path, filename, file_extension)

    return _to_file_meta_read(meta)
