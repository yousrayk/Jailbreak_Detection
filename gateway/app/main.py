import csv
import json
import logging
import os
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("gateway")


def load_messages(csv_path: str) -> list[str]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row["prompt"] for row in reader]


def send(session: "requests.Session", url: str, message: str) -> "requests.Response":
    return session.post(url, json={"message": message}, timeout=10)


def replay(csv_path: str, url: str, delay_seconds: float, session=None, sleep_fn=time.sleep) -> None:
    """Reads every prompt from csv_path and POSTs it to the producer, one at
    a time, pacing sends with delay_seconds — this is what drives the whole
    pipeline end to end (see ARCHITECTURE.md's data flow diagram)."""
    session = session or requests.Session()
    for message in load_messages(csv_path):
        resp = send(session, url, message)
        if resp.status_code == 200:
            logger.info(json.dumps({"event": "sent", "id": resp.json().get("id"), "status": resp.status_code}))
        else:
            logger.error(json.dumps({"event": "send_failed", "status": resp.status_code, "body": resp.text}))
        sleep_fn(delay_seconds)


def run():
    csv_path = os.environ.get("CSV_PATH", "/app/test.csv")
    url = os.environ.get("GATEWAY_URL", "http://producer:5000/send")
    delay_seconds = float(os.environ.get("SEND_DELAY_SECONDS", "0.2"))
    replay(csv_path, url, delay_seconds)
    logger.info(json.dumps({"event": "replay_complete"}))


if __name__ == "__main__":
    run()
