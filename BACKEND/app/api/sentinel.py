from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal

from app.models.sentinel import (
    SentinelPreviewRequest,
    SentinelAvailabilityRequest,
    SentinelExtractRequest,
    SentinelClosestRequest
)

from app.services.gee import get_sentinel_composite

import ee
from datetime import datetime, timedelta

router = APIRouter(prefix="/sentinel", tags=["Sentinel"])


# ===============================
# DATABASE DEPENDENCY
# ===============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===============================
# AVAILABILITY YEAR
# ===============================
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


# ===============================
# AVAILABILITY MONTH
# ===============================
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


# ===============================
# PREVIEW SENTINEL
# ===============================
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


# ===============================
# EXTRACT NDVI TO SAMPLING POINTS
# ===============================
@router.post("/extract/{project_id}")
def extract_sentinel(
    project_id: str,
    payload: SentinelExtractRequest,
    db: Session = Depends(get_db)
):
    try:
        image_id = payload.image_id
        start_date = payload.start_date
        end_date = payload.end_date
        cloud = payload.cloud

        # ======================================
        # 1️ Load selected Sentinel image
        # ======================================
        image = ee.Image(image_id)

        # Get acquisition date from metadata
        img_date = ee.Date(image.get("system:time_start")) \
                      .format("YYYY-MM-dd") \
                      .getInfo()

        # ======================================
        # 2️ Get approved points in date range
        # ======================================
        points = db.execute(
            text("""
                SELECT id,
                       ST_X(geom) AS lon,
                       ST_Y(geom) AS lat
                FROM sampling_points
                WHERE project_id = :pid
                  AND survey_status = 'approved'
                  AND submitted_at BETWEEN :start AND :end
            """),
            {
                "pid": project_id,
                "start": start_date,
                "end": end_date
            }
        ).mappings().all()

        if not points:
            raise HTTPException(404, "No approved points in date range")

        processed = 0

        # ======================================
        # 3️ Extract for each point
        # ======================================
        for p in points:

            point_geom = ee.Geometry.Point([p["lon"], p["lat"]])

            stats = image.select(["B4", "B8"]).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point_geom.buffer(10),
                scale=10,
                maxPixels=1e9
            ).getInfo()

            if not stats:
                continue

            b4 = stats.get("B4")
            b8 = stats.get("B8")

            if b4 is None or b8 is None:
                continue

            ndvi = (b8 - b4) / (b8 + b4) if (b8 + b4) != 0 else 0

            # ======================================
            # 4️ Save to DB (TRACEABLE)
            # ======================================
            db.execute(
                text("""
                    UPDATE sampling_points
                    SET
                        ndvi = :ndvi,
                        b4 = :b4,
                        b8 = :b8,
                        sentinel_date = :img_date,
                        sentinel_cloud = :cloud,
                        sentinel_image_id = :image_id
                    WHERE id = :id
                """),
                {
                    "id": p["id"],
                    "ndvi": ndvi,
                    "b4": b4,
                    "b8": b8,
                    "img_date": img_date,
                    "cloud": cloud,
                    "image_id": image_id
                }
            )

            processed += 1

        db.commit()

        return {
            "status": "success",
            "image_id": image_id,
            "sentinel_date": img_date,
            "processed_points": processed
        }

    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/list-closest-scenes/{project_id}")
def list_closest_scenes(
    project_id: str,
    payload: SentinelClosestRequest,
    db: Session = Depends(get_db)
):
    try:
        # ===============================
        # 1️ Get Project AOI
        # ===============================
        project = db.execute(
            text("""
                SELECT ST_AsGeoJSON(aoi)::json AS aoi
                FROM projects
                WHERE id = :pid
            """),
            {"pid": project_id}
        ).mappings().first()

        if not project:
            raise HTTPException(404, "Project not found")

        aoi = ee.Geometry(project["aoi"])

        # ===============================
        # 2️ Compute Mid Date
        # ===============================
        start_date = payload.start_date
        end_date = payload.end_date

        delta = end_date - start_date
        mid_date = start_date + timedelta(days=delta.days / 2)


        search_start = mid_date - timedelta(days=30)
        search_end = mid_date + timedelta(days=30)

        # ===============================
        # 3️ Search Sentinel Collection
        # ===============================
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(search_start.isoformat(), search_end.isoformat())
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", payload.cloud))
        )

        # ===============================
        # 4️ Add Temporal Difference
        # ===============================
        def add_diff(img):
            img_date = ee.Date(img.get("system:time_start"))
            diff = img_date.difference(
                ee.Date(mid_date.isoformat()), "day"
            ).abs()
            return img.set("date_diff", diff)

        collection = collection.map(add_diff)

        # Sort by closest date
        collection = collection.sort("date_diff").limit(5)

        images = collection.getInfo()["features"]

        if not images:
            return []

        results = []

        for img in images:
            props = img["properties"]

            results.append({
                "image_id": img["id"],
                "date": datetime.utcfromtimestamp(
                    props["system:time_start"] / 1000
                ).strftime("%Y-%m-%d"),
                "cloud": props.get("CLOUDY_PIXEL_PERCENTAGE", 0),
                "date_diff": round(props.get("date_diff", 0), 1)
            })

        return results

    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/preview-image")
def preview_image(payload: dict):

    image_id = payload.get("image_id")

    if not image_id:
        raise HTTPException(400, "image_id required")

    image = ee.Image(image_id)

    map_id = image.getMapId({
        "bands": ["B4","B3","B2"],
        "min": 0,
        "max": 3000
    })

    return {
        "tile_url": map_id["tile_fetcher"].url_format
    }
