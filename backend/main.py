"""Application entry point for local and package-based execution.

Supports:
- `uvicorn main:app --reload` from the `backend` directory.
- `uvicorn backend.main:app --reload` from the repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure absolute imports like `backend.api` resolve when running:
# `cd backend && uvicorn main:app --reload`
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.api import app
from backend.config import API_HOST, API_PORT


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
