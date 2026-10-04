from fastapi.testclient import TestClient

from app.main import RAW_TOPIC, app, get_publisher
from app.publisher import FakePublisher

fake = FakePublisher()
app.dependency_overrides[get_publisher] = lambda: fake

client = TestClient(app)


def test_send_publishes_to_raw_topic():
    resp = client.post("/send", json={"message": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body

    topic, payload = fake.published[-1]
    assert topic == RAW_TOPIC
    assert payload["message"] == "hello"
    assert payload["schema_version"] == 1
    assert payload["id"] == body["id"]
    assert "produced_at" in payload


def test_rejects_empty_message():
    resp = client.post("/send", json={"message": ""})
    assert resp.status_code == 422


def test_rejects_missing_message_field():
    resp = client.post("/send", json={})
    assert resp.status_code == 422


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
