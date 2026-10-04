RAW_TOPIC = "persistent://public/default/messages.raw"
PREDICTIONS_TOPIC = "persistent://public/default/predictions.result"


def build_joined_payload(message: dict, prediction: dict) -> dict:
    return {
        "id": message["id"],
        "message": message["message"],
        "classification": prediction["classification"],
        "confidence": prediction["confidence"],
        "model_version": prediction["model_version"],
    }
