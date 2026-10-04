from app.transforms import build_joined_payload


def test_build_joined_payload_matches_contract():
    message = {
        "schema_version": 1,
        "id": "abc-123",
        "message": "hello",
        "produced_at": "2026-01-01T00:00:00+00:00",
    }
    prediction = {
        "schema_version": 1,
        "id": "abc-123",
        "classification": "jailbreak",
        "confidence": 0.9,
        "model_version": "albert_production@100",
        "predicted_at": "2026-01-01T00:00:01+00:00",
    }

    payload = build_joined_payload(message, prediction)

    assert payload == {
        "id": "abc-123",
        "message": "hello",
        "classification": "jailbreak",
        "confidence": 0.9,
        "model_version": "albert_production@100",
    }
