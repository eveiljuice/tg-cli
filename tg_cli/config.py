"""Configuration loading for tg-cli."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path.home() / ".tg-cli"
CONFIG_FILE = APP_DIR / "config.toml"
SESSION_PATH = APP_DIR / "session"
DOWNLOADS_DIR = APP_DIR / "downloads"
LOG_FILE = APP_DIR / "tg-cli.log"


@dataclass
class Config:
    api_id: int = 0
    api_hash: str = ""
    session_path: str = str(SESSION_PATH)
    download_path: str = str(DOWNLOADS_DIR)
    messages_per_page: int = 50


def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load config from .env, then ~/.tg-cli/config.toml, return Config."""
    ensure_dirs()
    load_dotenv()

    api_id_str = os.getenv("API_ID", "")
    api_hash = os.getenv("API_HASH", "")

    if not api_id_str or not api_hash:
        if CONFIG_FILE.exists():
            try:
                if sys.version_info >= (3, 11):
                    import tomllib
                else:
                    import tomli as tomllib
                with open(CONFIG_FILE, "rb") as f:
                    data = tomllib.load(f)
                tg = data.get("telegram", {})
                api_id_str = str(tg.get("api_id", api_id_str))
                api_hash = tg.get("api_hash", api_hash)
            except Exception:
                pass

    api_id = int(api_id_str) if api_id_str else 0

    return Config(
        api_id=api_id,
        api_hash=api_hash,
    )


def save_credentials(api_id: int, api_hash: str) -> None:
    """Save API credentials to ~/.tg-cli/config.toml."""
    ensure_dirs()
    import tomli_w

    data: dict = {}
    if CONFIG_FILE.exists():
        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
            with open(CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            pass

    data.setdefault("telegram", {})
    data["telegram"]["api_id"] = api_id
    data["telegram"]["api_hash"] = api_hash

    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)
