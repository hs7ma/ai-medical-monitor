import os
import sys

os.environ["POSTGRES_HOST"] = "localhost"
os.environ["MQTT_BROKER"] = "localhost"
os.environ["INFLUXDB_URL"] = "http://localhost:8086"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"

from fastapi.testclient import TestClient


def test_health():
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("OK: /health ->", data)


def test_root():
    from app.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ai-medical-monitor"
    print("OK: / ->", data)


def test_openapi():
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AI Medical Monitor API"
    paths = list(schema["paths"].keys())
    print("OK: /openapi.json ->", len(paths), "paths")
    assert "/api/auth/login" in paths
    assert "/api/patients" in paths
    assert "/api/beds" in paths
    assert "/api/alerts" in paths


if __name__ == "__main__":
    test_health()
    test_root()
    test_openapi()
    print("\nAll tests passed!")
