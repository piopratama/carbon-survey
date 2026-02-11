from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class SurveyProjectCreate(BaseModel):
    name: str
    purpose: str
    location_name: str
    geometry: Dict[str, Any]
    year: int
    months: List[int]
    notes: Optional[str] = None
    survey_area: Optional[Dict[str, Any]] = None
    survey_points: Optional[List[Dict[str, Any]]] = None
