from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from space_climate_ai.data import DatasetConfig, build_dataset, save_dataset
from space_climate_ai.train import train_model


def main() -> None:
    data_path = ROOT_DIR / "data" / "satellite_climate_data.csv"
    artifacts_path = ROOT_DIR / "artifacts"

    config = DatasetConfig(n_days=365, n_regions=24, seed=42)
    df = build_dataset(config)
    save_dataset(df, data_path)

    artifacts = train_model(data_path, artifacts_path, seed=42)
    metrics = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))

    print("Pipeline finished successfully.")
    print(f"Dataset: {data_path}")
    print(f"Model: {artifacts.model_path}")
    print(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()
