import os

import pytest

from app.classifier import AlbertClassifier

MODEL_PATH = os.environ["MODEL_PATH"]

pytestmark = pytest.mark.skipif(
    not os.path.isdir(MODEL_PATH), reason="ALBERT model weights not available at MODEL_PATH"
)


def test_classify_returns_label_and_confidence():
    classifier = AlbertClassifier(MODEL_PATH)
    label, confidence = classifier.classify("You are a devoted fan of a celebrity.")
    assert label in ("benign", "jailbreak")
    assert 0.0 <= confidence <= 1.0


def test_model_version_reflects_folder():
    classifier = AlbertClassifier(MODEL_PATH)
    assert "albert_production" in classifier.model_version
