"""Message input widget — bottom panel for composing messages."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class MessageInput(Widget, can_focus=True):
    DEFAULT_CSS = """
    MessageInput {
        height: auto;
        max-height: 5;
        width: 100%;
        border-top: solid $primary;
        padding: 0 1;
    }

    #reply-context {
        height: 1;
        color: $text-muted;
        display: none;
    }

    #reply-context.visible {
        display: block;
    }
    """

    class Submitted(Message):
        def __init__(self, text: str, reply_to: int | None = None) -> None:
            self.text = text
            self.reply_to = reply_to
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self._reply_to: int | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="reply-context")
        yield Input(placeholder="Type a message...", id="msg-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        self.post_message(self.Submitted(text=text, reply_to=self._reply_to))
        event.input.value = ""
        self.clear_reply()

    def set_reply(self, message_id: int, preview: str) -> None:
        self._reply_to = message_id
        ctx = self.query_one("#reply-context", Static)
        ctx.update(f"Replying to: {preview[:50]}")
        ctx.add_class("visible")

    def clear_reply(self) -> None:
        self._reply_to = None
        try:
            ctx = self.query_one("#reply-context", Static)
            ctx.update("")
            ctx.remove_class("visible")
        except Exception:
            pass

    def focus(self, scroll_visible: bool = True) -> None:
        try:
            self.query_one("#msg-input", Input).focus(scroll_visible)
        except Exception:
            pass
