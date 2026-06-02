from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from space_climate_ai.api import run_api_server


if __name__ == "__main__":
    run_api_server(host="127.0.0.1", port=8000)
