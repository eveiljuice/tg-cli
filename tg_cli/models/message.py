"""Message data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class MessageModel:
    id: int
    sender_id: int | None
    sender_name: str
    text: str
    date: datetime | None
    is_outgoing: bool
    reply_to_msg_id: int | None
    media_type: str | None  # "photo", "document", "video", "sticker", etc.
    media_file_name: str | None
    raw: Any  # raw Telethon message

    @property
    def local_date(self) -> datetime | None:
        if self.date:
            if self.date.tzinfo is not None:
                return self.date.astimezone(tz=None)
            return self.date
        return None

    @property
    def time_str(self) -> str:
        dt = self.local_date
        if dt:
            return dt.strftime("%H:%M")
        return ""

    @property
    def display_text(self) -> str:
        if self.text:
            return self.text
        if self.media_type:
            name = self.media_file_name or ""
            return f"[{self.media_type}] {name}".strip()
        return "[empty]"
