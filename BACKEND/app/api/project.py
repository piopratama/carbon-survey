from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from app.db.session import SessionLocal
from app.models.project import Project
from sqlalchemy import text


router = APIRouter(prefix="/projects", tags=["Projects"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_project(payload: dict, db: Session = Depends(get_db)):
    geom = shape(payload["geometry"])

    project = Project(
        name=payload["name"],
        aoi=from_shape(geom, srid=4326),
        year=payload["year"],
        months=payload["months"],
        cloud=payload.get("cloud", 20)
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": str(project.id),
        "name": project.name
    }

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
              ST_AsGeoJSON(
                ST_PointOnSurface(aoi)
              )::json AS center
            FROM projects
            ORDER BY created_at DESC;
        """)
    ).mappings().all()

    return rows

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    res = db.execute(
        text("DELETE FROM projects WHERE id = :id RETURNING id"),
        {"id": project_id}
    ).fetchone()

    if not res:
        raise HTTPException(404, "Project tidak ditemukan")

    db.commit()
    return {"deleted": project_id}
