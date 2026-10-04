from app.transforms import build_dlq_payload, build_prediction_payload


def test_build_prediction_payload_matches_contract():
    payload = build_prediction_payload("abc-123", "jailbreak", 0.987654, "albert_production@100")
    assert payload["schema_version"] == 1
    assert payload["id"] == "abc-123"
    assert payload["classification"] == "jailbreak"
    assert payload["confidence"] == 0.9877
    assert payload["model_version"] == "albert_production@100"
    assert "predicted_at" in payload


def test_build_dlq_payload_matches_contract():
    payload = build_dlq_payload('{"bad": "json"', "boom", stage="consumer_prediction")
    assert payload["schema_version"] == 1
    assert payload["original_payload"] == '{"bad": "json"'
    assert payload["error"] == "boom"
    assert payload["stage"] == "consumer_prediction"
    assert "failed_at" in payload
