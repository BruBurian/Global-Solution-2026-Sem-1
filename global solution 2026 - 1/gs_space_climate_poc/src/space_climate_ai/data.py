from __future__ import annotations

import csv
import datetime as dt
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetConfig:
    n_days: int = 365
    n_regions: int = 20
    seed: int = 42


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def build_dataset(config: DatasetConfig) -> list[dict[str, float | int | str]]:
    rng = random.Random(config.seed)
    first_day = dt.date(2025, 1, 1)

    rows: list[dict[str, float | int | str]] = []
    for region_idx in range(config.n_regions):
        region_id = f"R{region_idx + 1:02d}"

        base_temp = rng.uniform(20.0, 34.0)
        base_soil = rng.uniform(35.0, 75.0)
        vegetation = rng.uniform(0.2, 0.8)

        for day_idx in range(config.n_days):
            current_date = first_day + dt.timedelta(days=day_idx)
            seasonal_wave = 4.5 * math.sin(2 * math.pi * day_idx / 365)
            surface_temp_c = base_temp + seasonal_wave + rng.gauss(0, 1.8)

            cloud_cover_pct = _clip(rng.gauss(52, 18), 5, 100)
            rain_seed = rng.gammavariate(2.0, 5.0)
            rainfall_mm_7d = _clip(rain_seed * (cloud_cover_pct / 100) * 1.8, 0, 120)

            ndvi = _clip(vegetation + rng.gauss(0, 0.06) - (surface_temp_c - 28) * 0.01, 0.05, 0.95)
            soil_moisture_pct = _clip(base_soil + rainfall_mm_7d * 0.35 - surface_temp_c * 0.55 + rng.gauss(0, 3), 5, 95)
            evapotranspiration_mm = _clip(surface_temp_c * 0.22 + (100 - cloud_cover_pct) * 0.05 + rng.gauss(0, 0.8), 1.5, 16)

            drought_score = (
                0.28 * surface_temp_c
                - 0.12 * rainfall_mm_7d
                - 0.27 * soil_moisture_pct
                - 6.0 * ndvi
                + 1.5 * evapotranspiration_mm
                + rng.gauss(0, 1.6)
            )
            drought_risk = 1 if drought_score > -3.0 else 0

            rows.append(
                {
                    "date": current_date.isoformat(),
                    "region_id": region_id,
                    "surface_temp_c": round(surface_temp_c, 3),
                    "ndvi": round(ndvi, 4),
                    "rainfall_mm_7d": round(rainfall_mm_7d, 3),
                    "soil_moisture_pct": round(soil_moisture_pct, 3),
                    "cloud_cover_pct": round(cloud_cover_pct, 3),
                    "evapotranspiration_mm": round(evapotranspiration_mm, 3),
                    "drought_risk": drought_risk,
                }
            )

    return rows


def save_dataset(rows: list[dict[str, float | int | str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    headers = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
