import logging
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.direct.direct_runner import BundleBasedDirectRunner

from app.pipeline import build_pipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("consumer_join")


def run():
    output_path = os.environ.get("JOINED_RESULTS_PATH", "/data/joined_results.jsonl")
    # Bypass Prism entirely — see the same note in consumer_prediction/app/main.py.
    options = PipelineOptions(["--streaming"])
    with beam.Pipeline(runner=BundleBasedDirectRunner(), options=options) as pipeline:
        build_pipeline(pipeline, output_path)
    logger.info("Pipeline stopped.")


if __name__ == "__main__":
    run()
