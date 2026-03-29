"""Dialog data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DialogModel:
    id: int
    name: str
    unread_count: int
    last_message_text: str
    last_message_date: datetime | None
    is_group: bool
    is_channel: bool
    is_user: bool
    entity: Any  # raw Telethon entity

    @property
    def display_name(self) -> str:
        return self.name or "Unknown"

    @property
    def last_message_preview(self) -> str:
        text = self.last_message_text or ""
        if len(text) > 40:
            return text[:37] + "..."
        return text

    @property
    def icon(self) -> str:
        if self.is_channel:
            return "#"
        if self.is_group:
            return "@"
        return " "
