import json
from typing import Protocol


class Publisher(Protocol):
    def publish(self, topic: str, payload: dict) -> None: ...


class PulsarPublisher:
    """Real publisher, backed by a Pulsar client. One producer per topic, reused across sends."""

    def __init__(self, service_url: str):
        import pulsar

        self._client = pulsar.Client(service_url)
        self._producers: dict[str, "pulsar.Producer"] = {}

    def publish(self, topic: str, payload: dict) -> None:
        if topic not in self._producers:
            self._producers[topic] = self._client.create_producer(topic)
        self._producers[topic].send(json.dumps(payload).encode("utf-8"))

    def close(self) -> None:
        self._client.close()


class FakePublisher:
    """In-memory publisher for unit tests — no Pulsar broker needed."""

    def __init__(self):
        self.published: list[tuple[str, dict]] = []

    def publish(self, topic: str, payload: dict) -> None:
        self.published.append((topic, payload))
