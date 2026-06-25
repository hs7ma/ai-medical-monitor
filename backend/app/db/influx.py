from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from app.core.config import settings


def get_influx_client() -> InfluxDBClient:
    return InfluxDBClient(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG,
        timeout=30_000,
    )


def write_vitals(data: dict) -> None:
    from influxdb_client import Point, WritePrecision
    from datetime import datetime, timezone

    point = (
        Point("vital_signs")
        .tag("bed_id", str(data.get("bed_id", "unknown")))
        .tag("patient_id", str(data.get("patient_id", "unknown")))
        .field("spo2", float(data.get("spo2", 0.0)))
        .field("heart_rate", float(data.get("heart_rate", 0.0)))
        .field("temperature", float(data.get("temperature", 0.0)))
        .field("confidence", int(data.get("confidence", 0)))
        .field("finger_detected", 1 if data.get("finger_detected") else 0)
        .field("wifi_rssi", int(data.get("wifi_rssi", 0)))
        .time(datetime.now(timezone.utc), WritePrecision.S)
    )

    client = get_influx_client()
    try:
        with client.write_api(write_options=SYNCHRONOUS) as write_api:
            write_api.write(bucket=settings.INFLUXDB_BUCKET, record=point)
    finally:
        client.close()


def query_vitals(bed_id: str, minutes: int = 60) -> list[dict]:
    from influxdb_client.client.query_api import QueryOptions

    client = get_influx_client()
    try:
        query_api = client.query_api()
        flux = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -{minutes}m)
          |> filter(fn: (r) => r._measurement == "vital_signs")
          |> filter(fn: (r) => r.bed_id == "{bed_id}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"])
        '''
        tables = query_api.query(flux)
        results = []
        for table in tables:
            for record in table.records:
                results.append(
                    {
                        "time": record.get_time().isoformat(),
                        "bed_id": record.values.get("bed_id"),
                        "patient_id": record.values.get("patient_id"),
                        "spo2": record.values.get("spo2"),
                        "heart_rate": record.values.get("heart_rate"),
                        "temperature": record.values.get("temperature"),
                        "confidence": record.values.get("confidence"),
                    }
                )
        return results
    finally:
        client.close()
