from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
import math
import ee

router = APIRouter(prefix="/carbon", tags=["Carbon"])


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
# SIMPLE LINEAR REGRESSION (NO SKLEARN)
# y = b0 + b1*x1 + ... + bk*xk
# ===============================
def fit_linear_regression(X, y):
    # Add intercept column
    # X: list[list[float]] shape (n,k)
    # y: list[float] shape (n,)
    n = len(X)
    if n == 0:
        raise ValueError("No data")
    k = len(X[0])

    # Build design matrix with intercept
    A = []
    for i in range(n):
        A.append([1.0] + [float(v) for v in X[i]])

    # Solve normal equation: beta = (A^T A)^-1 A^T y
    # We'll do a small, safe Gauss-Jordan inversion for (k+1)x(k+1)
    m = k + 1

    # Compute ATA and ATy
    ATA = [[0.0] * m for _ in range(m)]
    ATy = [0.0] * m

    for i in range(n):
        for r in range(m):
            ATy[r] += A[i][r] * y[i]
            for c in range(m):
                ATA[r][c] += A[i][r] * A[i][c]

    # Invert ATA (Gauss-Jordan)
    # Augment with identity
    aug = [row[:] + [0.0]*m for row in ATA]
    for i in range(m):
        aug[i][m+i] = 1.0

    # Elimination
    for col in range(m):
        # Find pivot
        pivot = col
        for r in range(col, m):
            if abs(aug[r][col]) > abs(aug[pivot][col]):
                pivot = r
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("Singular matrix (not enough variation / too few points)")

        # Swap
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        # Normalize row
        div = aug[col][col]
        for j in range(2*m):
            aug[col][j] /= div

        # Eliminate others
        for r in range(m):
            if r == col:
                continue
            factor = aug[r][col]
            for j in range(2*m):
                aug[r][j] -= factor * aug[col][j]

    inv = [row[m:] for row in aug]

    beta = [0.0] * m
    for r in range(m):
        beta[r] = sum(inv[r][c] * ATy[c] for c in range(m))

    intercept = beta[0]
    coefs = beta[1:]
    return intercept, coefs


def metrics(y_true, y_pred):
    n = len(y_true)
    if n == 0:
        return None

    mean_y = sum(y_true) / n
    ss_tot = sum((v - mean_y) ** 2 for v in y_true)
    ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else None

    mse = ss_res / n
    rmse = math.sqrt(mse)
    return r2, rmse


# ===============================
# TRAIN MODEL
# ===============================
@router.post("/train/{project_id}")
def train_carbon_model(project_id: str, db: Session = Depends(get_db)):
    # Choose features we will use
    features = ["ndvi", "evi", "b4", "b8"]

    # Pull training data from approved points
    rows = db.execute(
        text(f"""
            SELECT {",".join(features)}, agb_kg_per_m2
            FROM sampling_points
            WHERE project_id = :pid
              AND survey_status = 'approved'
              AND agb_kg_per_m2 IS NOT NULL
              AND ndvi IS NOT NULL
              AND b4 IS NOT NULL
              AND b8 IS NOT NULL
        """),
        {"pid": project_id}
    ).mappings().all()

    if len(rows) < 10:
        raise HTTPException(
            400,
            f"Data approved terlalu sedikit untuk training (butuh minimal ~10). Sekarang: {len(rows)}"
        )

    X = []
    y = []
    for r in rows:
        # if evi is missing, you can default to 0, but better require it if you want it
        xrow = []
        for f in features:
            if r[f] is None:
                raise HTTPException(400, f"Feature {f} masih NULL di beberapa point")
            xrow.append(float(r[f]))
        X.append(xrow)
        y.append(float(r["agb_kg_per_m2"]))

    try:
        intercept, coefs = fit_linear_regression(X, y)
    except ValueError as e:
        raise HTTPException(400, f"Gagal training: {str(e)}")

    # Predict on training set (baseline)
    yhat = []
    for i in range(len(X)):
        pred = intercept
        for j in range(len(features)):
            pred += coefs[j] * X[i][j]
        yhat.append(pred)

    r2, rmse = metrics(y, yhat)

    # Save to project_models
    inserted = db.execute(
        text("""
            INSERT INTO project_models (project_id, model_type, features, params, r_squared, rmse)
            VALUES (:pid, :model_type, :features, :params::jsonb, :r2, :rmse)
            RETURNING id
        """),
        {
            "pid": project_id,
            "model_type": "linear_regression",
            "features": features,
            "params": {
                "intercept": intercept,
                "coefficients": dict(zip(features, coefs)),
            },
            "r2": r2,
            "rmse": rmse
        }
    ).fetchone()

    db.commit()

    return {
        "project_id": project_id,
        "model_id": int(inserted[0]),
        "model_type": "linear_regression",
        "features": features,
        "params": {
            "intercept": intercept,
            "coefficients": dict(zip(features, coefs)),
        },
        "r_squared": r2,
        "rmse": rmse,
        "training_points": len(rows),
    }


# ===============================
# GENERATE CARBON MAP (GEE EXPORT)
# ===============================
@router.post("/generate/{project_id}")
def generate_carbon_map(project_id: str, db: Session = Depends(get_db)):
    # get project aoi + sentinel params
    proj = db.execute(
        text("""
            SELECT
              id,
              year,
              months,
              cloud,
              ST_AsGeoJSON(aoi)::json AS aoi
            FROM projects
            WHERE id = :pid
        """),
        {"pid": project_id}
    ).mappings().first()

    if not proj:
        raise HTTPException(404, "Project tidak ditemukan")

    # get latest model
    model = db.execute(
        text("""
            SELECT id, model_type, features, params
            FROM project_models
            WHERE project_id = :pid
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"pid": project_id}
    ).mappings().first()

    if not model:
        raise HTTPException(400, "Belum ada model. Jalankan /carbon/train/{project_id} dulu.")

    if model["model_type"] != "linear_regression":
        raise HTTPException(400, "Saat ini hanya support linear_regression")

    params = model["params"]
    intercept = float(params["intercept"])
    coef_map = params["coefficients"]  # dict feature->coef

    # build EE geometry
    aoi = ee.Geometry(proj["aoi"])

    # You already have this service
    from app.services.gee import get_sentinel_composite

    composite, ndvi = get_sentinel_composite(
        geometry=aoi,
        year=proj["year"],
        months=proj["months"],
        cloud=proj["cloud"] or 20,
    )

    # Ensure we have the bands needed
    # ndvi you already compute; for evi we can compute here
    # NOTE: Sentinel-2 SR: B2,B4,B8 are available
    b2 = composite.select("B2")
    b4 = composite.select("B4")
    b8 = composite.select("B8")

    # EVI = 2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)
    evi = b8.subtract(b4).multiply(2.5).divide(
        b8.add(b4.multiply(6)).subtract(b2.multiply(7.5)).add(1)
    ).rename("EVI")

    # Compose feature image with consistent names:
    feat_img = ee.Image.cat([
        ndvi.rename("NDVI"),
        evi.rename("EVI"),
        b4.rename("B4"),
        b8.rename("B8"),
    ])

    # Carbon prediction:
    # y = intercept + sum(coef[f]*band)
    # Map your DB features to our band names:
    band_lookup = {
        "ndvi": "NDVI",
        "evi": "EVI",
        "b4": "B4",
        "b8": "B8",
    }

    pred = ee.Image.constant(intercept)
    for f, coef in coef_map.items():
        band = band_lookup.get(f)
        if not band:
            raise HTTPException(400, f"Feature tidak dikenali: {f}")
        pred = pred.add(feat_img.select(band).multiply(float(coef)))

    pred = pred.rename("AGB_kg_m2").clip(aoi)

    # Export to Drive by default (simple + works everywhere)
    # If you use Cloud Storage instead, we can switch.
    task = ee.batch.Export.image.toDrive(
        image=pred,
        description=f"carbon_{project_id}",
        folder="carbon_outputs",
        fileNamePrefix=f"carbon_{project_id}",
        region=aoi,
        scale=10,
        maxPixels=1e13
    )
    task.start()

    # store to project_outputs
    out = db.execute(
        text("""
            INSERT INTO project_outputs (project_id, output_type, gee_task_id, stats)
            VALUES (:pid, :otype, :task_id, :stats::jsonb)
            RETURNING id
        """),
        {
            "pid": project_id,
            "otype": "carbon_map",
            "task_id": task.id,
            "stats": {
                "model_id": model["id"],
                "year": proj["year"],
                "months": proj["months"],
                "cloud": proj["cloud"],
                "export": "drive",
                "scale": 10
            }
        }
    ).fetchone()

    db.commit()

    return {
        "project_id": project_id,
        "output_id": int(out[0]),
        "gee_task_id": task.id,
        "message": "Export started (Drive folder: carbon_outputs)"
    }
