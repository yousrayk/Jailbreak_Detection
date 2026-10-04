import logging
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.direct.direct_runner import BundleBasedDirectRunner

from app.pipeline import build_pipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("consumer_prediction")


def run():
    model_path = os.environ["MODEL_PATH"]
    # Instantiate BundleBasedDirectRunner directly instead of going through
    # "--runner=DirectRunner" (which resolves to SwitchingDirectRunner):
    # newer apache-beam's SwitchingDirectRunner defaults streaming pipelines
    # to an external "Prism" sidecar process (a Go binary it downloads at
    # runtime), which crashed (SIGSEGV) in this container. Bypassing the
    # selection logic avoids Prism entirely, no flag combination disables it.
    options = PipelineOptions(["--streaming"])
    with beam.Pipeline(runner=BundleBasedDirectRunner(), options=options) as pipeline:
        build_pipeline(pipeline, model_path)
    logger.info("Pipeline stopped.")


if __name__ == "__main__":
    run()
