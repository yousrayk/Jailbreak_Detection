import os

# Convenience default for local (non-Docker) test runs on this machine, where
# the ALBERT weights live in the original prototype repo. In Docker, MODEL_PATH
# is set explicitly via docker-compose to the bind-mounted path instead.
DEFAULT_MODEL_PATH = r"C:\Users\PC\Downloads\Jailbreak-Detection-main\saved_models\albert_production"
os.environ.setdefault("MODEL_PATH", DEFAULT_MODEL_PATH)
