from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from datetime import date
import ast
import math

router = APIRouter(prefix="/survey", tags=["Survey"])


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
# SAFE FORMULA EVAL
# ===============================
_ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Call,
)

_ALLOWED_FUNCS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pow": pow,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
}


def safe_eval_formula(expr: str, variables: dict) -> float:
    tree = ast.parse(expr, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError(f"Komponen tidak diizinkan: {type(node).__name__}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
                raise ValueError("Function tidak diizinkan")

        if isinstance(node, ast.Name):
            if node.id not in variables and node.id not in _ALLOWED_FUNCS:
                raise ValueError(f"Variable tidak dikenal: {node.id}")

    compiled = compile(tree, "<formula>", "eval")
    env = {"__builtins__": {}}
    env.update(_ALLOWED_FUNCS)

    val = eval(compiled, env, variables)

    return float(val)


# ===============================
# CREATE SURVEY (TREE MEASUREMENT)
# ===============================
@router.post("/tree/{sampling_point_id}")
def create_tree_survey(
    sampling_point_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    surveyor_id = payload.get("surveyor_id")
    tree_species_id = payload.get("tree_species_id")
    dbh_cm = payload.get("dbh_cm")

    circumference_cm = payload.get("circumference_cm")
    height_m = payload.get("height_m")
    description = payload.get("description")

    lat_in = payload.get("latitude")
    lng_in = payload.get("longitude")

    if not surveyor_id:
        raise HTTPException(400, "surveyor_id wajib diisi")
    if not tree_species_id:
        raise HTTPException(400, "tree_species_id wajib diisi")
    if dbh_cm is None:
        raise HTTPException(400, "dbh_cm wajib diisi")

    # ===============================
    # 1) CHECK SAMPLING POINT
    # ===============================
    point = db.execute(
        text("""
            SELECT
                id,
                approval_status,
                latitude,
                longitude,
                ST_Y(geom) AS geom_lat,
                ST_X(geom) AS geom_lng
            FROM sampling_points
            WHERE id = :pid
        """),
        {"pid": sampling_point_id}
    ).mappings().first()

    if not point:
        raise HTTPException(404, "Sampling point tidak ditemukan")

    if str(point["approval_status"]) == "approved":
        raise HTTPException(400, "Sampling point sudah approved")

    # ===============================
    # 2) CHECK SURVEYOR JOINED
    # ===============================
    joined = db.execute(
        text("""
            SELECT 1
            FROM sampling_assignments
            WHERE sampling_point_id = :pid
              AND surveyor_id = :sid
            LIMIT 1
        """),
        {"pid": sampling_point_id, "sid": surveyor_id}
    ).scalar()

    if not joined:
        raise HTTPException(403, "Anda belum join sampling point ini")

    # ===============================
    # 3) GET TREE SPECIES
    # ===============================
    species = db.execute(
        text("""
            SELECT
                id,
                local_name,
                scientific_name,
                wood_density,
                biomass_formula,
                description,
                leaf_photo_url,
                trunk_photo_url,
                tree_photo_url
            FROM tree_species
            WHERE id = :id
        """),
        {"id": tree_species_id}
    ).mappings().first()

    if not species:
        raise HTTPException(404, "Tree species tidak ditemukan")

    # ===============================
    # 4) LAT/LNG RESOLUTION
    # ===============================
    lat = lat_in
    lng = lng_in

    if lat is None or lng is None:
        lat = point["latitude"] if point["latitude"] is not None else point["geom_lat"]
        lng = point["longitude"] if point["longitude"] is not None else point["geom_lng"]

    if lat is None or lng is None:
        raise HTTPException(400, "Latitude/Longitude tidak tersedia")

    # ===============================
    # 5) BIOMASS CALCULATION
    # ===============================
    dbh = float(dbh_cm)
    height = float(height_m) if height_m else None
    wd = float(species["wood_density"]) if species["wood_density"] else None
    formula = species["biomass_formula"]

    if not formula or not formula.strip():

        # DEFAULT SIMPLE FORMULA
        if height and wd:
            biomass = 0.11 * wd * (dbh ** 2) * height
        elif wd:
            biomass = 0.11 * wd * (dbh ** 2)
        else:
            biomass = 0.11 * (dbh ** 2)

    else:
        variables = {
            "dbh_cm": dbh,
            "height_m": height if height else 0.0,
            "circumference_cm": float(circumference_cm) if circumference_cm else 0.0,
            "wood_density": wd if wd else 0.0,
        }

        try:
            biomass = safe_eval_formula(formula, variables)
        except ValueError as e:
            raise HTTPException(400, f"biomass_formula error: {str(e)}")

    # ===============================
    # 6) INSERT SURVEY
    # ===============================
    row = db.execute(
        text("""
            INSERT INTO surveys (
                sampling_point_id,
                surveyor_id,
                tree_species_id,
                survey_date,
                dbh_cm,
                circumference_cm,
                height_m,
                biomass,
                description,
                latitude,
                longitude,
                geom,
                status
            )
            VALUES (
                :sampling_point_id,
                :surveyor_id,
                :tree_species_id,
                CURRENT_DATE,
                :dbh_cm,
                :circumference_cm,
                :height_m,
                :biomass,
                :description,
                :latitude,
                :longitude,
                ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                'draft'
            )
            RETURNING id, survey_date
        """),
        {
            "sampling_point_id": sampling_point_id,
            "surveyor_id": surveyor_id,
            "tree_species_id": tree_species_id,
            "dbh_cm": dbh_cm,
            "circumference_cm": circumference_cm,
            "height_m": height_m,
            "biomass": biomass,
            "description": description,
            "latitude": lat,
            "longitude": lng,
        }
    ).mappings().first()

    db.commit()

    return {
        "survey_id": row["id"],
        "sampling_point_id": sampling_point_id,
        "survey_date": str(row["survey_date"]) if row["survey_date"] else str(date.today()),
        "latitude": float(lat),
        "longitude": float(lng),
        "biomass": float(biomass),
        "tree_species": {
            "id": species["id"],
            "local_name": species["local_name"],
            "scientific_name": species["scientific_name"],
            "description": species["description"],
            "leaf_photo_url": species["leaf_photo_url"],
            "trunk_photo_url": species["trunk_photo_url"],
            "tree_photo_url": species["tree_photo_url"],
        }
    }

# ===============================
# ADD PHOTOS TO SURVEY
# ===============================
@router.post("/{survey_id}/photos")
def add_survey_photos(
    survey_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Payload:
    {
        "photos": [
            "http://127.0.0.1:8000/uploads/surveys/abc.jpg",
            "http://127.0.0.1:8000/uploads/surveys/xyz.jpg"
        ]
    }
    """

    photos = payload.get("photos")

    if not photos or not isinstance(photos, list):
        raise HTTPException(400, "photos harus berupa list URL")

    # check survey exists
    exists = db.execute(
        text("SELECT id FROM surveys WHERE id = :id"),
        {"id": survey_id}
    ).scalar()

    if not exists:
        raise HTTPException(404, "Survey tidak ditemukan")

    inserted = []

    for url in photos:
        row = db.execute(
            text("""
                INSERT INTO survey_photos (
                    survey_id,
                    photo_url
                )
                VALUES (
                    :survey_id,
                    :photo_url
                )
                RETURNING id
            """),
            {
                "survey_id": survey_id,
                "photo_url": url
            }
        ).mappings().first()

        inserted.append(row["id"])

    db.commit()

    return {
        "survey_id": survey_id,
        "photos_added": len(inserted),
        "photo_ids": inserted
    }

# ===============================
# SUBMIT SURVEY
# ===============================
@router.post("/{survey_id}/submit")
def submit_survey(
    survey_id: int,
    db: Session = Depends(get_db)
):
    """
    Change survey status from draft -> submitted
    """

    survey = db.execute(
        text("""
            SELECT id, status
            FROM surveys
            WHERE id = :id
        """),
        {"id": survey_id}
    ).mappings().first()

    if not survey:
        raise HTTPException(404, "Survey tidak ditemukan")

    if survey["status"] != "draft":
        raise HTTPException(400, "Survey sudah disubmit atau diproses")

    db.execute(
        text("""
            UPDATE surveys
            SET
                status = 'submitted',
                reviewed_at = NULL
            WHERE id = :id
        """),
        {"id": survey_id}
    )

    db.commit()

    return {
        "survey_id": survey_id,
        "status": "submitted"
    }

@router.get("/by-point/{point_id}")
def list_surveys_by_point(point_id: int, db: Session = Depends(get_db)):

    rows = db.execute(
        text("""
            SELECT
                s.id AS survey_id,
                s.tree_species_id,
                s.dbh_cm,
                s.height_m,
                s.biomass,
                s.latitude,
                s.longitude,
                s.created_at,
                u.name AS input_by_name,
                ts.local_name
            FROM surveys s
            JOIN tree_species ts ON ts.id = s.tree_species_id
            JOIN users u ON u.id = s.surveyor_id
            WHERE s.sampling_point_id = :pid
            ORDER BY s.created_at ASC
        """),
        {"pid": point_id}
    ).mappings().all()

    result = []

    for r in rows:

        photos = db.execute(
            text("""
                SELECT photo_url
                FROM survey_photos
                WHERE survey_id = :sid
                ORDER BY id ASC
            """),
            {"sid": r["survey_id"]}
        ).scalars().all()

        result.append({
            "survey_id": r["survey_id"],
            "tree_species_id": r["tree_species_id"],
            "dbh_cm": r["dbh_cm"],
            "height_m": r["height_m"],
            "biomass": r["biomass"],
            "latitude": float(r["latitude"]) if r["latitude"] else None,
            "longitude": float(r["longitude"]) if r["longitude"] else None,
            "input_by_name": r["input_by_name"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "tree_species": {
                "local_name": r["local_name"]
            },
            "photo1": photos[0] if len(photos) > 0 else None,
            "photo2": photos[1] if len(photos) > 1 else None,
            "photo3": photos[2] if len(photos) > 2 else None,
        })

    return result



@router.put("/{survey_id}")
def update_survey(
    survey_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            UPDATE surveys
            SET
                tree_species_id = :species,
                dbh_cm = :dbh,
                height_m = :height,
                latitude = :lat,
                longitude = :lng
            WHERE id = :id
            RETURNING id
        """),
        {
            "id": survey_id,
            "species": payload.get("tree_species_id"),
            "dbh": payload.get("dbh_cm"),
            "height": payload.get("height_m"),
            "lat": payload.get("latitude"),
            "lng": payload.get("longitude")
        }
    ).fetchone()

    if not result:
        raise HTTPException(404, "Survey not found")

    db.commit()

    return {"status": "updated"}

@router.delete("/{survey_id}")
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            DELETE FROM surveys
            WHERE id = :id
            RETURNING id
        """),
        {"id": survey_id}
    ).fetchone()

    if not result:
        raise HTTPException(404, "Survey not found")

    db.commit()

    return {"deleted": survey_id}

@router.post("/{survey_id}/photos-single")
def save_survey_photos_single(
    survey_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    db.execute(text("""
        DELETE FROM survey_photos
        WHERE survey_id = :sid
    """), {"sid": survey_id})

    for key in ["photo1","photo2","photo3"]:
        url = payload.get(key)
        if url:
            db.execute(text("""
                INSERT INTO survey_photos (survey_id, photo_url)
                VALUES (:sid, :url)
            """), {"sid": survey_id, "url": url})

    db.commit()
    return {"status":"ok"}
