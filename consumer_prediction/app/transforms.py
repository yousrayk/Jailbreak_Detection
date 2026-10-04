from datetime import datetime, timezone

SCHEMA_VERSION = 1
RAW_TOPIC = "persistent://public/default/messages.raw"
RESULT_TOPIC = "persistent://public/default/predictions.result"
DLQ_TOPIC = "persistent://public/default/messages.dlq"


def build_prediction_payload(
    raw_id: str, classification: str, confidence: float, model_version: str
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": raw_id,
        "classification": classification,
        "confidence": round(confidence, 4),
        "model_version": model_version,
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }


def build_dlq_payload(original_payload: str, error: str, stage: str = "consumer_prediction") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "original_payload": original_payload,
        "error": error,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
    }
