from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal

router = APIRouter(prefix="/sampling", tags=["Sampling"])


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
# GENERATE GRID SAMPLING
# ===============================
@router.post("/generate/{project_id}")
def generate_sampling(
    project_id: str,
    spacing_m: int = 50,
    db: Session = Depends(get_db),
):
    if spacing_m < 10:
        raise HTTPException(400, "spacing terlalu kecil")

    project = db.execute(
        text("SELECT id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).first()

    if not project:
        raise HTTPException(404, "Project tidak ditemukan")

    # Hapus hanya titik open
    db.execute(
        text("""
            DELETE FROM sampling_points
            WHERE project_id = :pid
            AND status = 'open';
        """),
        {"pid": project_id},
    )

    # Generate grid
    db.execute(
        text("""
        INSERT INTO sampling_points (project_id, geom, status)
        SELECT
          p.id,
          ST_Transform(ST_Centroid(g.geom), 4326),
          'open'
        FROM projects p
        JOIN LATERAL
          ST_SquareGrid(
            :spacing,
            ST_Transform(p.aoi, 3857)
          ) AS g
        ON ST_Intersects(
          ST_Transform(p.aoi, 3857),
          g.geom
        )
        WHERE p.id = :pid;
        """),
        {
            "pid": project_id,
            "spacing": spacing_m,
        },
    )

    db.commit()

    count = db.execute(
        text("""
          SELECT COUNT(*) FROM sampling_points
          WHERE project_id = :pid
        """),
        {"pid": project_id},
    ).scalar()

    return {
        "project_id": project_id,
        "spacing_m": spacing_m,
        "total_points": count,
    }


# ===============================
# LIST SAMPLING POINTS (WITH LAT/LNG)
# ===============================
@router.get("/points/{project_id}")
def list_sampling_points(project_id: str, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
            SELECT
              sp.id,
              sp.status,
              sp.survey_status,
              sp.start_date,
              sp.end_date,
              sp.description,
              sp.max_surveyors,
              sp.created_at,

              ST_AsGeoJSON(sp.geom)::json AS geometry,
              ST_Y(sp.geom) AS latitude,
              ST_X(sp.geom) AS longitude,

              COUNT(DISTINCT sa.surveyor_id) AS assigned_count,

              COALESCE(
                ARRAY_AGG(DISTINCT u.id) FILTER (WHERE u.id IS NOT NULL),
                '{}'
              ) AS assigned_ids,

              COALESCE(
                ARRAY_AGG(DISTINCT u.name) FILTER (WHERE u.name IS NOT NULL),
                '{}'
              ) AS assigned_names,

              COALESCE(b.total_biomass, 0) AS total_biomass

            FROM sampling_points sp

            LEFT JOIN sampling_assignments sa
              ON sa.sampling_point_id = sp.id

            LEFT JOIN users u
              ON u.id = sa.surveyor_id

            -- FIXED: aggregate biomass separately to avoid duplication
            LEFT JOIN (
                SELECT
                    sampling_point_id,
                    SUM(biomass) AS total_biomass
                FROM surveys
                GROUP BY sampling_point_id
            ) b
              ON b.sampling_point_id = sp.id

            WHERE sp.project_id = :pid

            GROUP BY
              sp.id,
              sp.status,
              sp.survey_status,
              sp.start_date,
              sp.end_date,
              sp.description,
              sp.max_surveyors,
              sp.created_at,
              sp.geom,
              b.total_biomass

            ORDER BY sp.id ASC;
        """),
        {"pid": project_id}
    ).mappings().all()

    features = []

    for r in rows:
        features.append({
            "type": "Feature",
            "geometry": r["geometry"],
            "properties": {
                "id": r["id"],
                "status": r["status"],
                "survey_status": r["survey_status"],
                "assigned_count": int(r["assigned_count"]),
                "max_surveyors": r["max_surveyors"],
                "assigned_ids": r["assigned_ids"],
                "assigned_names": r["assigned_names"],
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "total_biomass": float(r["total_biomass"] or 0),
                "start_date": str(r["start_date"]) if r["start_date"] else None,
                "end_date": str(r["end_date"]) if r["end_date"] else None,
                "description": r["description"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


# ===============================
# MOVE POINT
# ===============================
@router.put("/{point_id}/move")
def move_sampling_point(
    point_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    lat = payload.get("lat")
    lng = payload.get("lng")

    if lat is None or lng is None:
        raise HTTPException(400, "lat dan lng wajib diisi")

    result = db.execute(
        text("""
          UPDATE sampling_points
          SET geom = ST_SetSRID(
            ST_MakePoint(:lng, :lat),
            4326
          )
          WHERE id = :id
            AND status = 'open'
        """),
        {"id": point_id, "lat": lat, "lng": lng}
    )

    if result.rowcount == 0:
        raise HTTPException(400, "Titik tidak bisa dipindahkan")

    db.commit()

    return {"status": "moved"}


# ===============================
# ADD MANUAL POINT
# ===============================
@router.post("/manual/{project_id}")
def add_manual_sampling_point(
    project_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    lat = payload.get("lat")
    lng = payload.get("lng")

    if lat is None or lng is None:
        raise HTTPException(400, "lat dan lng wajib diisi")

    project = db.execute(
        text("SELECT id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).first()

    if not project:
        raise HTTPException(404, "Project tidak ditemukan")

    inside = db.execute(
        text("""
          SELECT ST_Contains(
            p.aoi,
            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
          )
          FROM projects p
          WHERE p.id = :pid
        """),
        {"pid": project_id, "lat": lat, "lng": lng},
    ).scalar()

    if not inside:
        raise HTTPException(
            400,
            "Titik berada di luar area fokus"
        )

    row = db.execute(
        text("""
          INSERT INTO sampling_points (project_id, geom, status)
          VALUES (
            :pid,
            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
            'open'
          )
          RETURNING id;
        """),
        {"pid": project_id, "lat": lat, "lng": lng},
    ).fetchone()

    db.commit()

    return {
        "project_id": project_id,
        "point_id": row[0],
        "status": "open",
        "latitude": lat,
        "longitude": lng
    }


# ===============================
# LOCK / UNLOCK
# ===============================
@router.post("/lock/{point_id}")
def lock_sampling_point(point_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            UPDATE sampling_points
            SET status = 'locked'
            WHERE id = :id
            AND status = 'open'
        """),
        {"id": point_id}
    )

    if result.rowcount == 0:
        raise HTTPException(400, "Titik tidak bisa dikunci")

    db.commit()
    return {"status": "locked"}


@router.post("/unlock/{point_id}")
def unlock_sampling_point(point_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        text("""
          UPDATE sampling_points
          SET status = 'open'
          WHERE id = :id
            AND status = 'locked'
        """),
        {"id": point_id}
    )

    if result.rowcount == 0:
        raise HTTPException(400, "Titik tidak bisa di-unlock")

    db.commit()
    return {"status": "unlocked"}


# ===============================
# DELETE
# ===============================
@router.delete("/{point_id}")
def delete_sampling_point(point_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        text("""
          DELETE FROM sampling_points
          WHERE id = :id
          AND status = 'open'
          RETURNING id
        """),
        {"id": point_id}
    ).fetchone()

    if not result:
        raise HTTPException(400, "Titik terkunci / tidak ditemukan")

    db.commit()
    return {"deleted": point_id}


# ===============================
# PREVIEW COUNT
# ===============================
@router.get("/preview/{project_id}")
def preview_sampling_points(
    project_id: str,
    spacing: int = Query(50, ge=10),
    db: Session = Depends(get_db)
):
    sql = text("""
        SELECT COUNT(*) AS count
        FROM projects p
        JOIN LATERAL (
            SELECT ST_Centroid(g.geom) AS centroid
            FROM ST_SquareGrid(
              :spacing,
              ST_Transform(p.aoi, 3857)
            ) AS g
            WHERE ST_Contains(
              ST_Transform(p.aoi, 3857),
              ST_Centroid(g.geom)
            )
        ) AS c ON TRUE
        WHERE p.id = :project_id;
    """)

    count = db.execute(sql, {
        "project_id": project_id,
        "spacing": spacing
    }).scalar()

    return {
        "project_id": project_id,
        "spacing_m": spacing,
        "count": count
    }

@router.put("/setup/{point_id}")
def setup_survey_point(
    point_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):

    db.execute(
        text("""
            UPDATE sampling_points
            SET
                start_date = :start_date,
                end_date = :end_date,
                description = :description,
                max_surveyors = :max_surveyors,
                survey_status = 'ready'
            WHERE id = :id
        """),
        {
            "id": point_id,
            "start_date": payload.get("start_date"),
            "end_date": payload.get("end_date"),
            "description": payload.get("description"),
            "max_surveyors": payload.get("max_surveyors", 5)
        }
    )

    db.commit()

    return {"status": "ready"}

@router.post("/assign/{point_id}")
def assign_surveyor(
    point_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    surveyor_id = payload.get("surveyor_id")

    if not surveyor_id:
        raise HTTPException(400, "surveyor_id wajib diisi")

    point = db.execute(
        text("""
        SELECT max_surveyors, survey_status, approval_status
        FROM sampling_points
        WHERE id = :id
        """),
        {"id": point_id}
    ).mappings().first()

    if not point:
        raise HTTPException(404, "Point tidak ditemukan")

    if point["approval_status"] == "approved":
        raise HTTPException(400, "Survey sudah final dan tidak bisa diubah")

    # cek jumlah existing
    current_count = db.execute(
        text("""
        SELECT COUNT(*)
        FROM sampling_assignments
        WHERE sampling_point_id = :id
        """),
        {"id": point_id}
    ).scalar()

    if current_count >= point["max_surveyors"]:
        raise HTTPException(400, "Kuota sudah penuh")

    # insert assignment
    db.execute(
        text("""
        INSERT INTO sampling_assignments (sampling_point_id, surveyor_id)
        VALUES (:pid, :sid)
        ON CONFLICT DO NOTHING
        """),
        {"pid": point_id, "sid": surveyor_id}
    )

    # hitung ulang jumlah surveyor
    new_count = db.execute(
        text("""
        SELECT COUNT(*)
        FROM sampling_assignments
        WHERE sampling_point_id = :pid
        """),
        {"pid": point_id}
    ).scalar()

    # tentukan survey_status baru
    if new_count >= point["max_surveyors"]:
        new_status = "full"
    elif new_count > 0:
        new_status = "active"
    else:
        new_status = "ready"

    db.execute(
        text("""
        UPDATE sampling_points
        SET survey_status = :status
        WHERE id = :pid
        """),
        {"pid": point_id, "status": new_status}
    )

    db.commit()

    return {
        "status": "assigned",
        "new_survey_status": new_status
    }


@router.delete("/assign/{point_id}/{surveyor_id}")
def remove_surveyor(
    point_id: int,
    surveyor_id: str,
    db: Session = Depends(get_db)
):
    # cek approval status + max_surveyors
    point = db.execute(
        text("""
        SELECT approval_status, max_surveyors
        FROM sampling_points
        WHERE id = :pid
        """),
        {"pid": point_id}
    ).mappings().first()

    if not point:
        raise HTTPException(404, "Point tidak ditemukan")

    if point["approval_status"] == "approved":
        raise HTTPException(400, "Survey sudah final dan tidak bisa diubah")

    # hapus assignment
    result = db.execute(
        text("""
        DELETE FROM sampling_assignments
        WHERE sampling_point_id = :pid
        AND surveyor_id = :sid
        RETURNING surveyor_id
        """),
        {"pid": point_id, "sid": surveyor_id}
    ).fetchone()

    if not result:
        raise HTTPException(404, "Surveyor tidak ditemukan di titik ini")

    # hitung ulang jumlah surveyor
    count = db.execute(
        text("""
        SELECT COUNT(*)
        FROM sampling_assignments
        WHERE sampling_point_id = :pid
        """),
        {"pid": point_id}
    ).scalar()

    # update survey_status
    if count == 0:
        new_status = "ready"
    elif count >= point["max_surveyors"]:
        new_status = "full"
    else:
        new_status = "active"

    db.execute(
        text("""
        UPDATE sampling_points
        SET survey_status = :status
        WHERE id = :pid
        """),
        {"pid": point_id, "status": new_status}
    )

    db.commit()

    return {
        "status": "removed",
        "new_survey_status": new_status
    }


@router.get("/assigned/{point_id}")
def get_assigned_surveyors(
    point_id: int,
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
        SELECT u.id, u.name
        FROM sampling_assignments sa
        JOIN users u ON u.id = sa.surveyor_id
        WHERE sa.sampling_point_id = :pid
        """),
        {"pid": point_id}
    ).mappings().all()

    return rows

@router.post("/submit/{point_id}")
def submit_sampling_point(
    point_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    surveyor_id = payload.get("surveyor_id")

    if not surveyor_id:
        raise HTTPException(400, "surveyor_id wajib diisi")

    # cek point
    point = db.execute(
        text("""
            SELECT survey_status, approval_status
            FROM sampling_points
            WHERE id = :pid
        """),
        {"pid": point_id}
    ).mappings().first()

    if not point:
        raise HTTPException(404, "Point tidak ditemukan")

    if point["approval_status"] == "approved":
        raise HTTPException(400, "Survey sudah final")

    if point["survey_status"] == "submitted":
        raise HTTPException(400, "Sudah disubmit")

    # cek surveyor sudah join
    joined = db.execute(
        text("""
            SELECT 1
            FROM sampling_assignments
            WHERE sampling_point_id = :pid
              AND surveyor_id = :sid
        """),
        {"pid": point_id, "sid": surveyor_id}
    ).scalar()

    if not joined:
        raise HTTPException(403, "Anda belum join titik ini")

    # update sampling point
    db.execute(
        text("""
            UPDATE sampling_points
            SET survey_status = 'submitted',
                submitted_at = NOW()
            WHERE id = :pid
        """),
        {"pid": point_id}
    )

    db.commit()

    return {"status": "submitted"}

# ===============================
# GET SINGLE SAMPLING POINT
# ===============================
@router.get("/point/{point_id}")
def get_sampling_point(
    point_id: int,
    db: Session = Depends(get_db)
):
    row = db.execute(
        text("""
            SELECT
              sp.id,
              sp.status,
              sp.survey_status,
              sp.start_date,
              sp.end_date,
              sp.description,
              sp.max_surveyors,
              sp.created_at,

              ST_Y(sp.geom) AS latitude,
              ST_X(sp.geom) AS longitude,

              COUNT(DISTINCT sa.surveyor_id) AS assigned_count,

              COALESCE(b.total_biomass, 0) AS total_biomass

            FROM sampling_points sp

            LEFT JOIN sampling_assignments sa
              ON sa.sampling_point_id = sp.id

            -- aggregate biomass separately
            LEFT JOIN (
                SELECT
                    sampling_point_id,
                    SUM(biomass) AS total_biomass
                FROM surveys
                GROUP BY sampling_point_id
            ) b
              ON b.sampling_point_id = sp.id

            WHERE sp.id = :id

            GROUP BY
              sp.id,
              sp.status,
              sp.survey_status,
              sp.start_date,
              sp.end_date,
              sp.description,
              sp.max_surveyors,
              sp.created_at,
              sp.geom,
              b.total_biomass
        """),
        {"id": point_id}
    ).mappings().first()

    if not row:
        raise HTTPException(404, "Point not found")

    return row
