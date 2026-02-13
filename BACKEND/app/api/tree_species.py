from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re

from app.db.session import get_db
from app.models.tree_species import TreeSpecies

router = APIRouter(prefix="/tree-species", tags=["Tree Species"])


# =====================
# DEFAULT FORMULA (NO HEIGHT)
# =====================

DEFAULT_BIOMASS_FORMULA = (
    "exp(-1.803 - 0.976 * log(wood_density) + "
    "2.673 * log(dbh) - 0.0299 * (log(dbh)**2))"
)


# =====================
# FORMULA NORMALIZER
# =====================

def normalize_formula(formula: str) -> str:
    """
    Normalize scientific notation to python-safe formula:
    - If empty -> use default formula
    - ln() -> log()
    - ^ -> **
    - lowercase common functions
    """

    # If empty or missing → use default
    if not formula or not str(formula).strip():
        return DEFAULT_BIOMASS_FORMULA

    f = formula.strip()

    # case insensitive ln -> log
    f = re.sub(r'\bln\s*\(', 'log(', f, flags=re.IGNORECASE)

    # replace ^ with **
    f = f.replace("^", "**")

    # lowercase common functions
    f = re.sub(r'\bEXP\b', 'exp', f, flags=re.IGNORECASE)
    f = re.sub(r'\bLOG\b', 'log', f, flags=re.IGNORECASE)

    return f


# ===================== LIST =====================
@router.get("")
def list_species(db: Session = Depends(get_db)):
    return db.query(TreeSpecies).order_by(TreeSpecies.local_name).all()


# ===================== GET BY ID =====================
@router.get("/{species_id}")
def get_species(species_id: int, db: Session = Depends(get_db)):
    species = db.get(TreeSpecies, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Tree species not found")
    return species


# ===================== CREATE =====================
@router.post("")
def create_species(payload: dict, db: Session = Depends(get_db)):

    normalized_formula = normalize_formula(
        payload.get("biomass_formula")
    )

    species = TreeSpecies(
        local_name=payload["local_name"],
        scientific_name=payload["scientific_name"],
        description=payload.get("description"),

        biomass_formula=normalized_formula,
        wood_density=payload.get("wood_density"),

        leaf_photo_url=payload.get("leaf_photo_url"),
        trunk_photo_url=payload.get("trunk_photo_url"),
        tree_photo_url=payload.get("tree_photo_url"),
    )

    db.add(species)
    db.commit()
    db.refresh(species)
    return species


# ===================== UPDATE =====================
@router.put("/{species_id}")
def update_species(species_id: int, payload: dict, db: Session = Depends(get_db)):

    species = db.get(TreeSpecies, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Tree species not found")

    species.local_name = payload["local_name"]
    species.scientific_name = payload["scientific_name"]
    species.description = payload.get("description")

    species.biomass_formula = normalize_formula(
        payload.get("biomass_formula")
    )
    species.wood_density = payload.get("wood_density")

    species.leaf_photo_url = payload.get("leaf_photo_url")
    species.trunk_photo_url = payload.get("trunk_photo_url")
    species.tree_photo_url = payload.get("tree_photo_url")

    db.commit()
    db.refresh(species)
    return species


# ===================== DELETE =====================
@router.delete("/{species_id}")
def delete_species(species_id: int, db: Session = Depends(get_db)):

    species = db.get(TreeSpecies, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Tree species not found")

    db.delete(species)
    db.commit()

    return {"status": "deleted"}
