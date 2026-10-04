import json
import logging
import os

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger("consumer_prediction")

LABELS = {0: "benign", 1: "jailbreak"}


class AlbertClassifier:
    """Loads an ALBERT sequence-classification model and reloads it whenever
    its files change on disk, so a new model can be dropped in without a
    restart — matches the live-update behavior from the original prototype.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None
        self._tokenizer = None
        self._loaded_mtime: float = -1
        self._reload_if_needed()

    def _latest_mtime(self) -> float:
        files = [
            os.path.join(self.model_path, f)
            for f in os.listdir(self.model_path)
            if os.path.isfile(os.path.join(self.model_path, f))
        ]
        return max((os.path.getmtime(f) for f in files), default=0)

    def _reload_if_needed(self) -> None:
        mtime = self._latest_mtime()
        if self._model is not None and mtime <= self._loaded_mtime:
            return
        logger.info(json.dumps({"event": "model_load", "model_path": self.model_path}))
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self._model.to(self.device)
        self._model.eval()
        self._loaded_mtime = mtime

    @property
    def model_version(self) -> str:
        name = os.path.basename(self.model_path.rstrip("/\\"))
        return f"{name}@{int(self._loaded_mtime)}"

    def classify(self, text: str) -> tuple[str, float]:
        self._reload_if_needed()
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=512
        ).to(self.device)
        with torch.no_grad():
            logits = self._model(**inputs).logits
        prediction = int(torch.argmax(logits, dim=-1).item())
        confidence = torch.softmax(logits, dim=-1)[0][prediction].item()
        return LABELS[prediction], confidence
