from __future__ import annotations

import json
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .data import DatasetConfig, build_dataset, save_dataset
from .predict import DroughtRiskPredictor
from .train import train_model

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "artifacts" / "drought_model.json"
METRICS_PATH = BASE_DIR / "artifacts" / "metrics.json"
WEB_DIR = BASE_DIR / "web"
SEED_MIN = 0
SEED_MAX = 999999

EXPECTED_FIELDS = {
    "surface_temp_c",
    "ndvi",
    "rainfall_mm_7d",
    "soil_moisture_pct",
    "cloud_cover_pct",
    "evapotranspiration_mm",
}


def run_pipeline_now(seed: int = 42) -> dict[str, object]:
    data_path = BASE_DIR / "data" / "satellite_climate_data.csv"
    artifacts_path = BASE_DIR / "artifacts"

    config = DatasetConfig(n_days=365, n_regions=24, seed=seed)
    rows = build_dataset(config)
    save_dataset(rows, data_path)

    artifacts = train_model(data_path, artifacts_path, seed=seed)
    metrics = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))

    return {
        "status": "ok",
        "seed": seed,
        "dataset_rows": len(rows),
        "model_path": str(artifacts.model_path),
        "metrics": metrics,
    }


class APIHandler(BaseHTTPRequestHandler):
    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send_bytes(status, body, "application/json")

    def _serve_static(self, relative_path: str) -> bool:
        safe_path = relative_path.lstrip("/")
        if not safe_path:
            safe_path = "index.html"

        file_path = WEB_DIR / safe_path
        if not file_path.exists() or not file_path.is_file():
            return False

        suffix = file_path.suffix.lower()
        if suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        else:
            content_type = "application/octet-stream"

        body = file_path.read_bytes()
        self._send_bytes(200, body, content_type)
        return True

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html", "/styles.css", "/app.js"}:
            request_path = "/index.html" if self.path == "/" else self.path
            if self._serve_static(request_path):
                return

        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if self.path == "/metrics":
            if not METRICS_PATH.exists():
                self._send_json(404, {"error": "metrics_not_found", "detail": "Run the pipeline first."})
                return
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            self._send_json(200, metrics)
            return

        self._send_json(404, {"error": "route_not_found"})

    def do_POST(self) -> None:
        if self.path == "/run-pipeline":
            content_length = int(self.headers.get("Content-Length", "0"))
            request_bytes = self.rfile.read(content_length) if content_length > 0 else b""

            payload: dict[str, object] = {}
            if request_bytes:
                try:
                    decoded = json.loads(request_bytes.decode("utf-8"))
                except json.JSONDecodeError:
                    self._send_json(400, {"error": "invalid_json"})
                    return

                if not isinstance(decoded, dict):
                    self._send_json(400, {"error": "invalid_payload"})
                    return
                payload = decoded

            seed_raw = payload.get("seed", 42)
            if isinstance(seed_raw, bool):
                self._send_json(400, {"error": "invalid_seed", "detail": "Seed must be an integer."})
                return

            try:
                seed = int(seed_raw)
            except (TypeError, ValueError):
                self._send_json(400, {"error": "invalid_seed", "detail": "Seed must be an integer."})
                return

            if seed < SEED_MIN or seed > SEED_MAX:
                self._send_json(
                    400,
                    {
                        "error": "seed_out_of_range",
                        "min": SEED_MIN,
                        "max": SEED_MAX,
                    },
                )
                return

            started_at = time.perf_counter()
            try:
                result = run_pipeline_now(seed=seed)
            except Exception as exc:
                self._send_json(500, {"error": "pipeline_failed", "detail": str(exc)})
                return

            result["elapsed_seconds"] = round(time.perf_counter() - started_at, 3)
            self._send_json(200, result)
            return

        if self.path != "/predict":
            self._send_json(404, {"error": "route_not_found"})
            return

        if not MODEL_PATH.exists():
            self._send_json(404, {"error": "model_not_found", "detail": "Run run_pipeline.py first."})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        request_bytes = self.rfile.read(content_length)

        try:
            payload = json.loads(request_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return

        if not isinstance(payload, dict):
            self._send_json(400, {"error": "invalid_payload"})
            return

        missing = [field for field in EXPECTED_FIELDS if field not in payload]
        if missing:
            self._send_json(400, {"error": "missing_fields", "fields": missing})
            return

        try:
            clean_payload = {field: float(payload[field]) for field in EXPECTED_FIELDS}
        except (TypeError, ValueError):
            self._send_json(400, {"error": "invalid_types"})
            return

        predictor = DroughtRiskPredictor(MODEL_PATH)
        result = predictor.predict(clean_payload)
        self._send_json(200, result)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_api_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), APIHandler)
    print(f"API listening at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_api_server()
