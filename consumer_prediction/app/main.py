import logging
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from app.pipeline import build_pipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("consumer_prediction")


def run():
    model_path = os.environ["MODEL_PATH"]
    # direct_running_mode=in_memory keeps execution fully in-process — newer
    # apache-beam defaults streaming DirectRunner to an external "Prism"
    # sidecar process, which crashed (SIGSEGV) in this container.
    options = PipelineOptions(
        ["--streaming", "--runner=DirectRunner", "--direct_running_mode=in_memory"]
    )
    with beam.Pipeline(options=options) as pipeline:
        build_pipeline(pipeline, model_path)
    logger.info("Pipeline stopped.")


if __name__ == "__main__":
    run()
