from app.transforms import build_joined_payload


class JoinBuffer:
    """Buffers raw messages and predictions by id, in memory, and returns a
    joined payload as soon as both halves for an id have arrived — a
    stream-stream join. Single-process, in-memory: matches this build's
    non-HA, single-instance-per-service scope (see ARCHITECTURE.md
    "Scaling"). Each id is cleared after joining, so it can't rejoin on a
    stray duplicate delivery under at-least-once semantics.
    """

    def __init__(self):
        self._messages: dict[str, dict] = {}
        self._predictions: dict[str, dict] = {}

    def add_message(self, message: dict) -> dict | None:
        self._messages[message["id"]] = message
        return self._try_join(message["id"])

    def add_prediction(self, prediction: dict) -> dict | None:
        self._predictions[prediction["id"]] = prediction
        return self._try_join(prediction["id"])

    def _try_join(self, id_: str) -> dict | None:
        if id_ not in self._messages or id_ not in self._predictions:
            return None
        joined = build_joined_payload(self._messages.pop(id_), self._predictions.pop(id_))
        return joined
