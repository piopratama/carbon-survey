from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import User

from app.services.auth import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
def list_users(role: str | None = None, db: Session = Depends(get_db)):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.order_by(User.name).all()


@router.post("")
def create_user(payload: dict, db: Session = Depends(get_db)):
    user = User(
        name=payload["name"],
        email=payload["email"],
        password_hash=hash_password(payload["password"]),
        role=payload.get("role", "surveyor"),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    db.refresh(user)
    return user


@router.put("/{user_id}")
def update_user(user_id: str, payload: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = payload.get("name", user.name)
    user.email = payload.get("email", user.email)
    user.role = payload.get("role", user.role)

    if payload.get("password"):
        user.password_hash = hash_password(payload["password"])

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"status": "deleted"}
