from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.alert import Alert
from app.schemas.alert import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    status_filter: str = "active",
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    query = db.query(Alert)
    if status_filter and status_filter != "all":
        query = query.filter(Alert.status == status_filter)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.post("/{alert_id}/ack", response_model=AlertOut)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status == "acked":
        raise HTTPException(status_code=400, detail="Alert already acknowledged")
    alert.status = "acked"
    alert.acked_at = datetime.utcnow()
    alert.acked_by = user.id
    db.commit()
    db.refresh(alert)
    return alert
