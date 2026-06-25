from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import require_role, get_current_user_ws
from app.db.influx import query_vitals
from app.models.user import User, UserRole
from app.models.bed import Bed
from app.models.patient import Patient
from app.schemas.bed import BedOut, BedAssign, VitalReading
from app.services.ws_hub import ws_hub

router = APIRouter(prefix="/api/beds", tags=["beds"])


@router.get("", response_model=List[BedOut])
def list_beds(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    return db.query(Bed).all()


@router.get("/{bed_id}/vitals", response_model=List[VitalReading])
def get_bed_vitals(
    bed_id: str,
    minutes: int = 60,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return query_vitals(bed_id, minutes=minutes)


@router.post("/{bed_id}/assign", response_model=BedOut)
def assign_patient(
    bed_id: str,
    payload: BedAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if payload.patient_id:
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        bed.patient_id = payload.patient_id
        bed.status = "occupied"
    else:
        bed.patient_id = None
        bed.status = "available"
    db.commit()
    db.refresh(bed)
    return bed


@router.websocket("/ws/stream")
async def bed_stream(websocket: WebSocket, db: Session = Depends(get_db)):
    user = get_current_user_ws(websocket, db)
    if not user:
        await websocket.close(code=4001)
        return
    await ws_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_hub.disconnect(websocket)
