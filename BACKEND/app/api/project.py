from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from app.db.session import SessionLocal
from app.models.project import Project


router = APIRouter(prefix="/projects", tags=["Projects"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= CREATE PROJECT =================
@router.post("/")
def create_project(payload: dict, db: Session = Depends(get_db)):
    geom = shape(payload["geometry"])

    project = Project(
        name=payload["name"],
        aoi=from_shape(geom, srid=4326),
        year=payload["year"],
        months=payload["months"],
        cloud=payload.get("cloud", 20),
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": str(project.id),
        "name": project.name,
    }


# ================= LIST PROJECTS =================
@router.get("/")
def list_projects(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT
              id,
              name,
              year,
              status,
              created_at,
              ST_AsGeoJSON(aoi)::json AS aoi,
              ST_AsGeoJSON(ST_PointOnSurface(aoi))::json AS center
            FROM projects
            ORDER BY created_at DESC;
        """)
    ).mappings().all()

    return rows


# ================= DELETE PROJECT =================
@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    res = db.execute(
        text("DELETE FROM projects WHERE id = :id RETURNING id"),
        {"id": project_id},
    ).fetchone()

    if not res:
        raise HTTPException(404, "Project tidak ditemukan")

    db.commit()
    return {"deleted": project_id}


# ================= FEATURE REPORT =================
@router.get("/{project_id}/feature-report")
def feature_report(project_id: str, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
            SELECT
                sp.id AS sampling_point_id,

                COALESCE(
                    STRING_AGG(s.id::text, ',' ORDER BY s.id),
                    ''
                ) AS survey_ids,

                COUNT(s.id) AS survey_count,

                sp.ndvi,
                sp.evi,
                sp.b4,
                sp.b8,

                COALESCE(
                    sp.latitude,
                    ST_Y(ST_Transform(sp.geom, 4326))
                ) AS latitude,

                COALESCE(
                    sp.longitude,
                    ST_X(ST_Transform(sp.geom, 4326))
                ) AS longitude,

                sp.start_date,
                sp.end_date,
                sp.sentinel_date,

                COALESCE(SUM(s.biomass), 0) AS total_biomass

            FROM sampling_points sp

            LEFT JOIN surveys s
                ON s.sampling_point_id = sp.id

            WHERE sp.project_id = :project_id
              AND sp.survey_status = 'approved'

            GROUP BY
                sp.id,
                sp.ndvi,
                sp.evi,
                sp.b4,
                sp.b8,
                sp.latitude,
                sp.longitude,
                sp.geom,
                sp.start_date,
                sp.end_date,
                sp.sentinel_date

            ORDER BY sp.id;
        """),
        {"project_id": project_id},
    ).mappings().all()

    return rows
