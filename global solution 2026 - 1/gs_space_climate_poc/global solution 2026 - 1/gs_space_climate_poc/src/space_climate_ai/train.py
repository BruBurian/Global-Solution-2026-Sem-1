from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

FEATURE_COLUMNS = [
    "surface_temp_c",
    "ndvi",
    "rainfall_mm_7d",
    "soil_moisture_pct",
    "cloud_cover_pct",
    "evapotranspiration_mm",
]
TARGET_COLUMN = "drought_risk"


@dataclass(frozen=True)
class TrainArtifacts:
    model_path: Path
    metrics_path: Path


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return 1 / (1 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1 + exp_pos)


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _standardize_fit(rows: list[list[float]]) -> tuple[list[float], list[float]]:
    if not rows:
        raise ValueError("No rows available for standardization")

    n_features = len(rows[0])
    means = [0.0] * n_features
    stds = [0.0] * n_features

    for col in range(n_features):
        col_values = [row[col] for row in rows]
        mean = sum(col_values) / len(col_values)
        variance = sum((value - mean) ** 2 for value in col_values) / len(col_values)
        std = math.sqrt(variance)

        means[col] = mean
        stds[col] = std if std > 1e-12 else 1.0

    return means, stds


def _standardize_transform(rows: list[list[float]], means: list[float], stds: list[float]) -> list[list[float]]:
    transformed: list[list[float]] = []
    for row in rows:
        transformed.append([(value - means[idx]) / stds[idx] for idx, value in enumerate(row)])
    return transformed


def _accuracy(y_true: list[int], y_pred: list[int]) -> float:
    hits = sum(int(a == b) for a, b in zip(y_true, y_pred))
    return hits / len(y_true) if y_true else 0.0


def _f1_score(y_true: list[int], y_pred: list[int]) -> float:
    tp = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y_true, y_pred) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0


def _roc_auc(y_true: list[int], y_score: list[float]) -> float:
    pairs = sorted(zip(y_score, y_true), key=lambda item: item[0])
    pos = sum(y_true)
    neg = len(y_true) - pos
    if pos == 0 or neg == 0:
        return 0.5

    rank_sum = 0.0
    for rank, (_, label) in enumerate(pairs, start=1):
        if label == 1:
            rank_sum += rank
    return (rank_sum - (pos * (pos + 1) / 2)) / (pos * neg)


def train_model(dataset_path: Path, artifacts_dir: Path, seed: int = 42) -> TrainArtifacts:
    with dataset_path.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        dataset = list(reader)

    if not dataset:
        raise ValueError("Dataset is empty")

    features: list[list[float]] = []
    targets: list[int] = []

    for row in dataset:
        features.append([float(row[column]) for column in FEATURE_COLUMNS])
        targets.append(int(row[TARGET_COLUMN]))

    rng = random.Random(seed)
    indexes = list(range(len(features)))
    rng.shuffle(indexes)

    test_size = int(len(indexes) * 0.25)
    test_idx = indexes[:test_size]
    train_idx = indexes[test_size:]

    x_train = [features[idx] for idx in train_idx]
    y_train = [targets[idx] for idx in train_idx]
    x_test = [features[idx] for idx in test_idx]
    y_test = [targets[idx] for idx in test_idx]

    means, stds = _standardize_fit(x_train)
    x_train_std = _standardize_transform(x_train, means, stds)
    x_test_std = _standardize_transform(x_test, means, stds)

    n_features = len(FEATURE_COLUMNS)
    weights = [0.0] * n_features
    bias = 0.0

    learning_rate = 0.04
    epochs = 450

    for _ in range(epochs):
        grad_w = [0.0] * n_features
        grad_b = 0.0

        for row, label in zip(x_train_std, y_train):
            probability = _sigmoid(_dot(weights, row) + bias)
            error = probability - label

            for idx in range(n_features):
                grad_w[idx] += error * row[idx]
            grad_b += error

        scale = 1.0 / len(x_train_std)
        for idx in range(n_features):
            weights[idx] -= learning_rate * grad_w[idx] * scale
        bias -= learning_rate * grad_b * scale

    y_proba = [_sigmoid(_dot(weights, row) + bias) for row in x_test_std]
    y_pred = [1 if proba >= 0.5 else 0 for proba in y_proba]

    metrics = {
        "accuracy": round(_accuracy(y_test, y_pred), 4),
        "f1": round(_f1_score(y_test, y_pred), 4),
        "roc_auc": round(_roc_auc(y_test, y_proba), 4),
        "rows_train": len(x_train),
        "rows_test": len(x_test),
        "model": "logistic_regression_from_scratch",
    }

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "drought_model.json"
    metrics_path = artifacts_dir / "metrics.json"

    model_blob = {
        "feature_columns": FEATURE_COLUMNS,
        "means": means,
        "stds": stds,
        "weights": weights,
        "bias": bias,
    }

    model_path.write_text(json.dumps(model_blob, indent=2), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return TrainArtifacts(model_path=model_path, metrics_path=metrics_path)
