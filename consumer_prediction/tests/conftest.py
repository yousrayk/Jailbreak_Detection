import os
from pathlib import Path

# Convenience default for local (non-Docker) test runs: weights copied into
# ./models/albert_production per README's "Model weights" section. In Docker,
# MODEL_PATH is set explicitly via docker-compose to the bind-mounted path
# instead.
DEFAULT_MODEL_PATH = str(
    Path(__file__).resolve().parents[2] / "models" / "albert_production"
)
os.environ.setdefault("MODEL_PATH", DEFAULT_MODEL_PATH)
