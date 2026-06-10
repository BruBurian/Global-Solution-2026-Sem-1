from __future__ import annotations

import json
import math
from pathlib import Path


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return 1 / (1 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1 + exp_pos)


class DroughtRiskPredictor:
    def __init__(self, model_path: Path) -> None:
        model_blob = json.loads(model_path.read_text(encoding="utf-8"))
        self.feature_columns: list[str] = model_blob["feature_columns"]
        self.means: list[float] = model_blob["means"]
        self.stds: list[float] = model_blob["stds"]
        self.weights: list[float] = model_blob["weights"]
        self.bias: float = model_blob["bias"]

    def predict(self, payload: dict[str, float]) -> dict[str, float | int | str]:
        raw = [float(payload[column]) for column in self.feature_columns]
        normalized = [
            (value - self.means[idx]) / self.stds[idx]
            for idx, value in enumerate(raw)
        ]

        linear_value = sum(
            weight * value for weight, value in zip(self.weights, normalized)
        ) + self.bias
        risk_probability = _sigmoid(linear_value)
        risk_label = int(risk_probability >= 0.5)

        return {
            "risk_probability": round(risk_probability, 4),
            "risk_label": risk_label,
            "risk_text": "high" if risk_label else "low",
        }
