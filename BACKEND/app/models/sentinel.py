from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date


# ===============================
# PREVIEW (for map visualization)
# ===============================
class SentinelPreviewRequest(BaseModel):
    geometry: Dict[str, Any]   # GeoJSON
    year: int
    months: List[int]
    cloud: int = 20


# ===============================
# AVAILABILITY CHECK
# ===============================
class SentinelAvailabilityRequest(BaseModel):
    geometry: Dict[str, Any]


# ===============================
# EXTRACT (for analysis page)
# ===============================
class SentinelExtractRequest(BaseModel):
    image_id: str
    start_date: date
    end_date: date
    cloud: int = 20

class SentinelClosestRequest(BaseModel):
    start_date: date
    end_date: date
    cloud: int = 50