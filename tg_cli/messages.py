"""Custom Textual messages for Telegram-to-TUI communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.message import Message


class AuthRequired(Message):
    """Telegram client is not authorized, show auth screen."""


@dataclass
class AuthComplete(Message):
    """Authorization succeeded."""
    user: Any  # Telethon User object


class CodeRequested(Message):
    """Verification code has been sent."""


class TwoFARequired(Message):
    """Two-factor authentication password needed."""


@dataclass
class AuthError(Message):
    """Authentication step failed."""
    error: str


@dataclass
class NewTelegramMessage(Message):
    """A new message arrived from Telegram."""
    message: Any  # MessageModel
    chat_id: int


@dataclass
class MessageEdited(Message):
    """A message was edited."""
    message: Any
    chat_id: int


@dataclass
class MessageDeleted(Message):
    """Messages were deleted."""
    message_ids: list[int]
    chat_id: int


@dataclass
class DialogsLoaded(Message):
    """Dialog list has been fetched."""
    dialogs: list


@dataclass
class MessagesLoaded(Message):
    """Messages for a chat have been fetched."""
    messages: list
    chat_id: int
    prepend: bool = False


@dataclass
class ConnectionStatusChanged(Message):
    """Connection state changed."""
    connected: bool
