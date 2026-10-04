import json
import logging
import os

import apache_beam as beam
import pulsar
from pulsar import Timeout

from app.join_buffer import JoinBuffer
from app.transforms import PREDICTIONS_TOPIC, RAW_TOPIC

logger = logging.getLogger("consumer_join")


class JoinDoFn(beam.DoFn):
    """Continuously reads both messages.raw and predictions.result, and
    emits a joined payload (as JSON) as soon as an id has arrived on both
    streams. Single impulse-triggered loop — same pattern as
    consumer_prediction's ReadFromPulsarDoFn."""

    def setup(self):
        service_url = os.environ["PULSAR_SERVICE_URL"]
        self.client = pulsar.Client(service_url)
        self.raw_consumer = self.client.subscribe(
            RAW_TOPIC,
            subscription_name="consumer-join-raw",
            consumer_type=pulsar.ConsumerType.Shared,
            initial_position=pulsar.InitialPosition.Earliest,
        )
        self.prediction_consumer = self.client.subscribe(
            PREDICTIONS_TOPIC,
            subscription_name="consumer-join-predictions",
            consumer_type=pulsar.ConsumerType.Shared,
            initial_position=pulsar.InitialPosition.Earliest,
        )
        self.buffer = JoinBuffer()

    def process(self, _):
        while True:
            joined = self._poll(self.raw_consumer, self.buffer.add_message)
            if joined:
                yield json.dumps(joined)
            joined = self._poll(self.prediction_consumer, self.buffer.add_prediction)
            if joined:
                yield json.dumps(joined)

    def _poll(self, consumer, add_fn):
        try:
            msg = consumer.receive(timeout_millis=200)
        except Timeout:
            return None
        try:
            payload = json.loads(msg.data().decode("utf-8"))
            joined = add_fn(payload)
            consumer.acknowledge(msg)
            return joined
        except Exception:
            logger.exception("Failed to process message; nacking.")
            consumer.negative_acknowledge(msg)
            return None

    def teardown(self):
        self.raw_consumer.close()
        self.prediction_consumer.close()
        self.client.close()


class WriteJoinedResultDoFn(beam.DoFn):
    """Sink: appends each joined result as a JSON line to a local file —
    a real destination instead of a dead-end print (see ARCHITECTURE.md's
    "Sink for joined result" decision)."""

    def __init__(self, output_path: str):
        self.output_path = output_path

    def setup(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def process(self, element: str):
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(element + "\n")
        logger.info(json.dumps({"event": "joined_result_written", "path": self.output_path}))


def build_pipeline(pipeline: beam.Pipeline, output_path: str) -> None:
    joined = (
        pipeline
        | "Trigger" >> beam.Create([None])
        | "Join" >> beam.ParDo(JoinDoFn())
    )
    _ = joined | "WriteResult" >> beam.ParDo(WriteJoinedResultDoFn(output_path))
