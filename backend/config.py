"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
DATABASE_URL: Final[str] = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'cyber_intelligence.db'}")
API_HOST: Final[str] = os.getenv("API_HOST", "0.0.0.0")
API_PORT: Final[int] = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
_default_origins = ",".join(
	[
		"http://localhost:3000",
		"http://127.0.0.1:3000",
		"http://localhost:5173",
		"http://127.0.0.1:5173",
	]
)
ALLOWED_ORIGINS: Final[list[str]] = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if origin.strip()]
ALLOWED_ORIGIN_REGEX: Final[str] = os.getenv(
	"ALLOWED_ORIGIN_REGEX",
	(
		r"^https://.*\.(app\.github\.dev|github\.dev)$"
		r"|^http://(10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(:3000|:5173)$"
	),
)
