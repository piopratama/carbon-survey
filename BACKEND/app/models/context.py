from pydantic import BaseModel
from typing import Dict, Any

class LocationContextRequest(BaseModel):
    name: str
    geometry: Dict[str, Any]
