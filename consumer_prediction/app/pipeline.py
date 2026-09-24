import json
import logging
import os

import apache_beam as beam
import pulsar
from pulsar import Timeout

from app.classifier import AlbertClassifier
from app.transforms import DLQ_TOPIC, RAW_TOPIC, RESULT_TOPIC, build_dlq_payload, build_prediction_payload

logger = logging.getLogger("consumer_prediction")

DLQ_TAG = "dlq"


class ReadFromPulsarDoFn(beam.DoFn):
    """Continuously receives raw messages from Pulsar. Triggered by a single
    impulse element; loops for the lifetime of the pipeline."""

    def setup(self):
        service_url = os.environ["PULSAR_SERVICE_URL"]
        self.client = pulsar.Client(service_url)
        self.consumer = self.client.subscribe(
            RAW_TOPIC,
            subscription_name="consumer-prediction",
            consumer_type=pulsar.ConsumerType.Shared,
            initial_position=pulsar.InitialPosition.Earliest,
        )

    def process(self, _):
        while True:
            try:
                msg = self.consumer.receive(timeout_millis=1000)
            except Timeout:
                continue
            try:
                yield msg.data().decode("utf-8")
                self.consumer.acknowledge(msg)
            except Exception:
                logger.exception("Failed to process received message; nacking.")
                self.consumer.negative_acknowledge(msg)

    def teardown(self):
        self.consumer.close()
        self.client.close()


class ClassifyDoFn(beam.DoFn):
    """Parses a raw message, runs it through the classifier, and emits a
    prediction payload — or a DLQ payload (tagged output) on any failure."""

    def __init__(self, model_path: str):
        self.model_path = model_path

    def setup(self):
        self.classifier = AlbertClassifier(self.model_path)

    def process(self, element: str):
        try:
            raw = json.loads(element)
            label, confidence = self.classifier.classify(raw["message"])
            payload = build_prediction_payload(
                raw["id"], label, confidence, self.classifier.model_version
            )
            yield json.dumps(payload)
        except Exception as e:
            logger.exception("Failed to classify message; routing to DLQ.")
            dlq_payload = build_dlq_payload(element, str(e))
            yield beam.pvalue.TaggedOutput(DLQ_TAG, json.dumps(dlq_payload))


class PublishDoFn(beam.DoFn):
    def __init__(self, topic: str):
        self.topic = topic

    def setup(self):
        service_url = os.environ["PULSAR_SERVICE_URL"]
        self.client = pulsar.Client(service_url)
        self.producer = self.client.create_producer(self.topic)

    def process(self, element: str):
        self.producer.send(element.encode("utf-8"))
        logger.info(json.dumps({"event": "published", "topic": self.topic}))

    def teardown(self):
        self.producer.close()
        self.client.close()


def build_pipeline(pipeline: beam.Pipeline, model_path: str) -> None:
    raw = (
        pipeline
        | "Trigger" >> beam.Create([None])
        | "ReadRaw" >> beam.ParDo(ReadFromPulsarDoFn())
    )
    classified = raw | "Classify" >> beam.ParDo(ClassifyDoFn(model_path)).with_outputs(
        DLQ_TAG, main="result"
    )
    _ = classified.result | "PublishResult" >> beam.ParDo(PublishDoFn(RESULT_TOPIC))
    _ = classified[DLQ_TAG] | "PublishDlq" >> beam.ParDo(PublishDoFn(DLQ_TOPIC))
