import asyncio
import json
import logging
import re
from typing import Optional

import aiomqtt

from app.core.config import settings
from app.db.influx import write_vitals
from app.services.ws_hub import ws_hub

logger = logging.getLogger(__name__)

_topic_re = re.compile(r"^hospital/bed/([^/]+)/vitals$")


def _save_vital_reading_to_sql(payload: dict):
    from app.db.session import SessionLocal
    from app.models.bed import Bed
    from app.models.vital_reading import VitalReading
    
    bed_id = payload.get("bed_id")
    if not bed_id:
        return
        
    db = SessionLocal()
    try:
        bed = db.query(Bed).filter(Bed.id == bed_id).first()
        if bed and bed.patient_id:
            reading = VitalReading(
                patient_id=bed.patient_id,
                spo2=payload.get("spo2"),
                heart_rate=payload.get("heart_rate"),
                temperature=payload.get("temperature"),
                confidence=payload.get("confidence", 0),
                source=payload.get("source", "sensor"),
            )
            db.add(reading)
            db.commit()
            logger.info("Saved vital reading from bed %s (patient %s) to SQLite", bed_id, bed.patient_id)
    except Exception as e:
        logger.error("Failed to save vital reading to SQLite: %s", e)
    finally:
        db.close()


class MQTTSubscriber:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("MQTT subscriber started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MQTT subscriber stopped")

    async def _run(self):
        while self._running:
            try:
                async with aiomqtt.Client(
                    hostname=settings.MQTT_BROKER,
                    port=settings.MQTT_PORT,
                ) as client:
                    await client.subscribe(settings.MQTT_TOPIC)
                    logger.info(
                        "Subscribed to %s on %s:%s",
                        settings.MQTT_TOPIC,
                        settings.MQTT_BROKER,
                        settings.MQTT_PORT,
                    )
                    async for message in client.messages:
                        await self._handle_message(message)
            except Exception as e:
                logger.error("MQTT connection error: %s — reconnecting in 5s", e)
                await asyncio.sleep(5)

    async def _handle_message(self, message):
        try:
            topic = str(message.topic)
            match = _topic_re.match(topic)
            if not match:
                return
            bed_id = match.group(1)
            payload = json.loads(message.payload.decode("utf-8"))
            payload["bed_id"] = bed_id

            await asyncio.to_thread(write_vitals, payload)
            await asyncio.to_thread(_save_vital_reading_to_sql, payload)
            await ws_hub.broadcast_vitals(payload)

        except json.JSONDecodeError:
            logger.warning("Invalid JSON on topic %s", message.topic)
        except Exception as e:
            logger.error("Error handling MQTT message: %s", e)


mqtt_subscriber = MQTTSubscriber()
