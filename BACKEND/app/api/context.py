from fastapi import APIRouter
from app.models.context import LocationContextRequest

router = APIRouter(prefix="/context", tags=["Context"])

@router.post("/location")
def set_location_context(payload: LocationContextRequest):
    return {
        "location_name": payload.name,
        "geometry": payload.geometry,
        "status": "context_set"
    }
