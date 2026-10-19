"""Settings loaded from the .env file next to pyproject.toml."""

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    bot_token: str
    tz: ZoneInfo
    db_path: Path


def load_config() -> Config:
    load_dotenv(PROJECT_DIR / ".env")
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN is missing: add it to the .env file")
    return Config(
        bot_token=token,
        tz=ZoneInfo(os.getenv("TZ_NAME", "Europe/Kyiv")),
        db_path=Path(os.getenv("DB_PATH", PROJECT_DIR / "sales.db")),
    )
