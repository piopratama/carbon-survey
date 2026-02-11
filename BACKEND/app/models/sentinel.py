from pydantic import BaseModel
from typing import List, Dict, Any

class SentinelPreviewRequest(BaseModel):
    geometry: Dict[str, Any]   # GeoJSON
    year: int
    months: List[int]
    cloud: int

class SentinelAvailabilityRequest(BaseModel):
    geometry: Dict[str, Any]
