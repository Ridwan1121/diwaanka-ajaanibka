"""Root entry point that re-exports the backend API app."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
BACKEND_APP = ROOT / "backend-api" / "app.py"
backend_path = str(BACKEND_APP.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

_spec = importlib.util.spec_from_file_location("backend_api_app", BACKEND_APP)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load backend app from {BACKEND_APP}")

_backend_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_backend_module)

app = _backend_module.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
