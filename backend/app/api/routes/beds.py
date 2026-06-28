from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import logging

from app.db.session import get_db
from app.api.deps import require_role, get_current_user_ws
from app.db.influx import query_vitals, write_vitals
from app.models.user import User, UserRole
from app.models.bed import Bed
from app.models.patient import Patient
from app.models.vital_reading import VitalReading as VitalReadingModel
from app.schemas.bed import BedOut, BedAssign, BedCreate, VitalReading, SensorVitalsCreate
from app.services.ws_hub import ws_hub

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/beds", tags=["beds"])


@router.get("", response_model=List[BedOut])
def list_beds(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    return db.query(Bed).all()


@router.post("", response_model=BedOut, status_code=201)
def create_bed(
    payload: BedCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    existing = db.query(Bed).filter(Bed.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bed already exists")
    bed = Bed(id=payload.id, room=payload.room, status="available")
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return bed


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


@router.post("/{bed_id}/vitals", status_code=201)
async def submit_sensor_vitals(
    bed_id: str,
    payload: SensorVitalsCreate,
    db: Session = Depends(get_db),
):
    """Receive vitals from an ESP32 sensor device over HTTP.

    Mirrors the MQTT subscriber pipeline: saves to SQLite, writes to
    InfluxDB, and broadcasts to connected WebSocket clients.
    """
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if not bed.patient_id:
        raise HTTPException(status_code=409, detail="No patient assigned to this bed")

    reading = VitalReadingModel(
        patient_id=bed.patient_id,
        spo2=payload.spo2,
        heart_rate=payload.heart_rate,
        temperature=payload.temperature,
        confidence=payload.confidence or 0,
        source=payload.source or "sensor",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    vital_data = {
        "bed_id": bed_id,
        "patient_id": bed.patient_id,
        "spo2": payload.spo2,
        "heart_rate": payload.heart_rate,
        "temperature": payload.temperature,
        "confidence": payload.confidence or 0,
        "finger_detected": payload.finger_detected,
        "wifi_rssi": payload.wifi_rssi or 0,
        "source": payload.source or "sensor",
    }

    try:
        await asyncio.to_thread(write_vitals, vital_data)
    except Exception as e:
        logger.warning("InfluxDB write failed for bed %s: %s", bed_id, e)

    await ws_hub.broadcast_vitals(vital_data)

    return {"status": "ok", "id": reading.id, "patient_id": bed.patient_id}


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
