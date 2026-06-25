from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserCreate
from app.core.security import hash_password
from app.models.user import User as UserModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    return db.query(UserModel).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    existing = db.query(UserModel).filter(UserModel.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    try:
        role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")
    new_user = UserModel(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=role,
        full_name=payload.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
