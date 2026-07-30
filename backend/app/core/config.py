import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "breastai.db"
# Local dev defaults to SQLite with no setup required. Production sets DATABASE_URL
# to a real PostgreSQL connection string (e.g. via Render/Railway), which takes over.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE_PATH}")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

PUBMED_API_KEY = os.getenv("PUBMED_API_KEY")

SNS_TIMEZONE = os.getenv("SNS_TIMEZONE", "Asia/Tokyo")
SNS_GENERATE_HOUR = int(os.getenv("SNS_GENERATE_HOUR", "7"))
SNS_PUBLISH_INTERVAL_MINUTES = int(os.getenv("SNS_PUBLISH_INTERVAL_MINUTES", "30"))

X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
# INSTAGRAM_ACCOUNT_ID is the current name; INSTAGRAM_BUSINESS_ACCOUNT_ID is kept as a
# fallback so existing deployments (e.g. Render) don't break before their env var is renamed.
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID") or os.getenv(
    "INSTAGRAM_BUSINESS_ACCOUNT_ID"
)


def _parse_hashtags(value: str | None) -> list[str]:
    if not value:
        return []
    return [tag.strip().lstrip("#") for tag in value.split(",") if tag.strip()]


# Optional, comma-separated hashtags appended to the Instagram caption per account persona.
INSTAGRAM_HASHTAGS_BY_ACCOUNT = {
    "doctor": _parse_hashtags(os.getenv("INSTAGRAM_HASHTAGS_DOCTOR")),
    "beauty": _parse_hashtags(os.getenv("INSTAGRAM_HASHTAGS_BEAUTY")),
}

THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
