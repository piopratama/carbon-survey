from fastapi import APIRouter, HTTPException
from app.models.sentinel import (
    SentinelPreviewRequest,
    SentinelAvailabilityRequest,
)
from app.services.gee import get_sentinel_composite
import ee
from datetime import datetime

router = APIRouter(prefix="/sentinel", tags=["Sentinel"])

@router.post("/availability")
def availability(payload: SentinelAvailabilityRequest):
    aoi = ee.Geometry(payload.geometry)
    collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(aoi)

    current_year = datetime.now().year

    def year_count(y):
        y = ee.Number(y)
        return ee.Feature(None, {
            "year": y,
            "count": collection.filterDate(
                ee.Date.fromYMD(y, 1, 1),
                ee.Date.fromYMD(y, 12, 31)
            ).size()
        })

    years = ee.List.sequence(2017, current_year)
    fc = ee.FeatureCollection(years.map(year_count)).getInfo()

    return {
        "years": [
            f["properties"]["year"]
            for f in fc["features"]
            if f["properties"]["count"] > 0
        ]
    }

@router.post("/availability/{year}")
def availability_month(year: int, payload: SentinelAvailabilityRequest):
    aoi = ee.Geometry(payload.geometry)
    collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(aoi)

    def month_count(m):
        m = ee.Number(m)
        start = ee.Date.fromYMD(year, m, 1)
        end = start.advance(1, "month")
        return ee.Feature(None, {
            "month": m,
            "count": collection.filterDate(start, end).size()
        })

    months = ee.List.sequence(1, 12)
    fc = ee.FeatureCollection(months.map(month_count)).getInfo()

    return {
        "year": year,
        "months": [
            f["properties"]["month"]
            for f in fc["features"]
            if f["properties"]["count"] > 0
        ]
    }

@router.post("/preview")
def preview_sentinel(payload: SentinelPreviewRequest):
    aoi = ee.FeatureCollection([payload.geometry]).geometry()

    composite, ndvi = get_sentinel_composite(
        geometry=aoi,
        year=payload.year,
        months=payload.months,
        cloud=payload.cloud,
    )

    true_color = composite.getMapId({
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
    })

    ndvi_map = ndvi.getMapId({
        "min": 0,
        "max": 1,
        "palette": ["white", "green"],
    })

    return {
        "true_color_url": true_color["tile_fetcher"].url_format,
        "ndvi_url": ndvi_map["tile_fetcher"].url_format,
    }

