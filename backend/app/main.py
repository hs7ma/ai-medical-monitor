import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Medical Monitor backend...")
    logger.info("Database: %s", "SQLite" if settings.USE_SQLITE else "PostgreSQL")

    from app.models.user import User
    from app.models.patient import Patient
    from app.models.bed import Bed
    from app.models.alert import Alert
    from app.models.medical_file import MedicalFile
    from app.models.diagnosis import Diagnosis
    from app.models.audit_log import AuditLog
    from app.models.chat import ChatSession, ChatMessage
    from app.models.vital_reading import VitalReading

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")

    _seed_admin()

    if not settings.USE_SQLITE:
        try:
            from app.services.storage import storage_service
            storage_service.ensure_bucket()
            logger.info("MinIO bucket ensured")
        except Exception as e:
            logger.warning("MinIO not available: %s", e)

    try:
        from app.services.mqtt_subscriber import mqtt_subscriber
        await mqtt_subscriber.start()
        logger.info("MQTT subscriber started")
    except Exception as e:
        logger.warning("MQTT not available: %s", e)

    logger.info("Startup complete")
    yield

    try:
        from app.services.mqtt_subscriber import mqtt_subscriber
        await mqtt_subscriber.stop()
    except Exception:
        pass
    logger.info("Shutdown complete")


def _seed_admin():
    from app.db.session import SessionLocal
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role=UserRole.admin,
                full_name="System Administrator",
            )
            doctor = User(
                username="doctor",
                password_hash=hash_password("doctor123"),
                role=UserRole.doctor,
                full_name="Dr. Demo",
            )
            nurse = User(
                username="nurse",
                password_hash=hash_password("nurse123"),
                role=UserRole.nurse,
                full_name="Nurse Demo",
            )
            db.add_all([admin, doctor, nurse])
            db.commit()
            logger.info("Seeded default users: admin/doctor/nurse")
    finally:
        db.close()


app = FastAPI(
    title="AI Medical Monitor API",
    description="Backend for AI-powered hospital monitoring and diagnosis system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import auth, patients, beds, uploads, alerts, admin, diagnosis, ml, vitals

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(beds.router)
app.include_router(uploads.router)
app.include_router(alerts.router)
app.include_router(admin.router)
app.include_router(diagnosis.router)
app.include_router(ml.router)
app.include_router(vitals.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "ai-medical-monitor", "version": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {
        "status": "healthy",
        "database": "sqlite" if settings.USE_SQLITE else "postgresql",
    }
