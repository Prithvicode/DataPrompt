from fastapi import APIRouter, UploadFile, File, HTTPException
from services.file_service import process_uploaded_file
from cache.storage import cached_datasets

router = APIRouter()

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    return await process_uploaded_file(file, cached_datasets)
