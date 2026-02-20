from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Request
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
    request: Request,
    file: UploadFile = File(...),
    category: str = Query("general")
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WebP images are allowed"
        )

    folder = BASE_DIR / category
    folder.mkdir(parents=True, exist_ok=True)

    ext = ALLOWED_MIME_TYPES[file.content_type]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = folder / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ambil base URL otomatis (works local & production)
    base_url = str(request.base_url).rstrip("/")

    return {
        "url": f"{base_url}/uploads/{category}/{filename}"
    }