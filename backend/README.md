# Backend — AI Medical Monitor

FastAPI backend for the AI-powered hospital monitoring and diagnosis system.

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI |
| MQTT client | aiomqtt (async) |
| Time-series DB | InfluxDB 2.x |
| Relational DB | PostgreSQL 16 (SQLAlchemy + Alembic) |
| File storage | MinIO (S3-compatible) |
| Auth | JWT + RBAC (passlib/bcrypt) |
| File processing | pdfplumber, Pillow, pytesseract (OCR) |

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app + lifespan (MQTT, seeding)
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   └── security.py      # JWT + password hashing
│   ├── db/
│   │   ├── session.py       # SQLAlchemy engine/session
│   │   └── influx.py        # InfluxDB read/write
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── services/
│   │   ├── mqtt_subscriber.py   # Async MQTT → InfluxDB + WebSocket
│   │   ├── ws_hub.py            # WebSocket broadcast hub
│   │   ├── storage.py           # MinIO file storage
│   │   └── file_processor.py    # PDF/OCR text extraction + image prep
│   └── api/
│       ├── deps.py          # Auth dependencies (RBAC)
│       └── routes/          # REST endpoints
├── alembic/                 # DB migrations
├── requirements.txt
├── Dockerfile
└── .env
```

## API Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | Login → JWT token |

### Patients
| Method | Path | Description | Role |
|---|---|---|---|
| GET | `/api/patients` | List patients | doctor/nurse/admin |
| POST | `/api/patients` | Create patient | doctor/admin |
| GET | `/api/patients/{id}` | Get patient | doctor/nurse/admin |

### Beds
| Method | Path | Description | Role |
|---|---|---|---|
| GET | `/api/beds` | List beds | doctor/nurse/admin |
| GET | `/api/beds/{id}/vitals` | Get vitals (InfluxDB) | doctor/nurse/admin |
| POST | `/api/beds/{id}/assign` | Assign patient to bed | doctor/admin |
| WS | `/api/beds/ws/stream` | Live vitals stream | authenticated |

### Uploads (Medical Files)
| Method | Path | Description | Role |
|---|---|---|---|
| POST | `/api/patients/{id}/uploads` | Upload PDF/image | doctor/admin |
| GET | `/api/patients/{id}/uploads` | List patient files | doctor/nurse/admin |
| GET | `/api/uploads/{id}` | Download file | doctor/nurse/admin |
| DELETE | `/api/uploads/{id}` | Delete file | doctor/admin |
| POST | `/api/uploads/{id}/extract` | Re-extract text (OCR/PDF) | doctor/admin |

### Alerts
| Method | Path | Description | Role |
|---|---|---|---|
| GET | `/api/alerts` | List alerts | doctor/nurse/admin |
| POST | `/api/alerts/{id}/ack` | Acknowledge alert | doctor/nurse/admin |

### Admin
| Method | Path | Description | Role |
|---|---|---|---|
| GET | `/api/admin/users` | List users | admin |
| POST | `/api/admin/users` | Create user | admin |

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | Health check |

## Default Users

Seeded on first startup:

| Username | Password | Role |
|---|---|---|
| admin | admin123 | admin |
| doctor | doctor123 | doctor |
| nurse | nurse123 | nurse |

> Change these in production!

## Running with Docker

From project root:

```bash
cp .env.example .env
docker compose up -d
```

Services:
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- InfluxDB: http://localhost:8086
- MinIO Console: http://localhost:9001

## Running locally (development)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Testing

```bash
cd backend
python test_app.py
```
