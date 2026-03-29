"""Media download/upload helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tg_cli.telegram.client import TelegramBridge


async def download_media(bridge: TelegramBridge, message: Any) -> str | None:
    """Download media from a message. Returns local file path or None."""
    download_dir = bridge.config.download_path
    os.makedirs(download_dir, exist_ok=True)
    try:
        path = await bridge.client.download_media(message, file=download_dir)
        return str(path) if path else None
    except Exception:
        return None


async def send_file(
    bridge: TelegramBridge, chat_id: int, file_path: str, caption: str = ""
) -> None:
    """Send a file to a chat."""
    entity = bridge._entity_cache.get(chat_id)
    if entity is None:
        entity = await bridge.client.get_entity(chat_id)
        bridge._entity_cache[chat_id] = entity
    await bridge.client.send_file(entity, file_path, caption=caption)
