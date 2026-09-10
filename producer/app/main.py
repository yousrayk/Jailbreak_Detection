import json
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI

from app.models import IncomingMessage
from app.publisher import Publisher, PulsarPublisher

SCHEMA_VERSION = 1
RAW_TOPIC = "persistent://public/default/messages.raw"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("producer")

app = FastAPI()
_publisher: Publisher | None = None


def get_publisher() -> Publisher:
    global _publisher
    if _publisher is None:
        service_url = os.environ.get("PULSAR_SERVICE_URL", "pulsar://pulsar:6650")
        _publisher = PulsarPublisher(service_url)
    return _publisher


def build_raw_message(message: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": str(uuid.uuid4()),
        "message": message,
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/send")
def send(incoming: IncomingMessage, publisher: Publisher = Depends(get_publisher)):
    raw = build_raw_message(incoming.message)
    publisher.publish(RAW_TOPIC, raw)
    logger.info(json.dumps({"event": "published", "id": raw["id"], "topic": RAW_TOPIC}))
    return {"id": raw["id"]}


@app.get("/health")
def health():
    return {"status": "ok"}
