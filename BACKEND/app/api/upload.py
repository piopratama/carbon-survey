from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pathlib import Path
import shutil
import uuid

router = APIRouter(prefix="/upload", tags=["Upload"])

BASE_DIR = Path("uploads")
BASE_DIR.mkdir(exist_ok=True)

ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp"
}

@router.post("")
def upload_image(
    file: UploadFile = File(...),
    category: str = Query("general")  # tree_species | surveys
):
    # Validasi hanya gambar
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WebP images are allowed"
        )

    folder = BASE_DIR / category
    folder.mkdir(parents=True, exist_ok=True)

    # Gunakan ekstensi berdasarkan MIME (lebih aman)
    ext = ALLOWED_MIME_TYPES[file.content_type]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = folder / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"http://127.0.0.1:8000/uploads/{category}/{filename}"
    }
