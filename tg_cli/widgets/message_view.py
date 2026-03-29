"""Message view widget — right panel showing messages in the selected chat."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from tg_cli.models.message import MessageModel


class MessageBubble(Static):
    DEFAULT_CSS = """
    MessageBubble {
        padding: 0 1;
        margin: 0;
        width: 100%;
    }
    """

    def __init__(self, msg: MessageModel) -> None:
        self.msg = msg
        super().__init__()

    def render(self) -> str:
        m = self.msg
        if m.is_outgoing:
            sender = "[bold cyan]You[/]"
        else:
            sender = f"[bold green]{m.sender_name}[/]"

        time = f"[dim]{m.time_str}[/]"
        reply = " [dim italic](reply)[/]" if m.reply_to_msg_id else ""

        text = m.display_text
        return f"{sender} {time}{reply}\n{text}"


class MessageView(Widget):
    DEFAULT_CSS = """
    MessageView {
        height: 1fr;
        width: 100%;
    }

    #chat-header {
        height: 1;
        background: #1a1a2e;
        padding: 0 1;
        width: 100%;
        color: #e0e0e0;
    }

    #messages-scroll {
        height: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._messages: list[MessageModel] = []

    def compose(self) -> ComposeResult:
        yield Static(" Select a chat", id="chat-header")
        yield VerticalScroll(id="messages-scroll")

    def set_chat_name(self, name: str) -> None:
        self.query_one("#chat-header", Static).update(f" {name}")

    def clear_messages(self) -> None:
        self._messages = []
        scroll = self.query_one("#messages-scroll", VerticalScroll)
        scroll.remove_children()

    def set_messages(self, messages: list[MessageModel]) -> None:
        self._messages = list(messages)
        scroll = self.query_one("#messages-scroll", VerticalScroll)
        scroll.remove_children()
        for msg in messages:
            scroll.mount(MessageBubble(msg))
        self._scroll_to_bottom()

    def append_message(self, msg: MessageModel) -> None:
        self._messages.append(msg)
        scroll = self.query_one("#messages-scroll", VerticalScroll)
        scroll.mount(MessageBubble(msg))
        self._scroll_to_bottom()

    def prepend_messages(self, messages: list[MessageModel]) -> None:
        self._messages = messages + self._messages
        scroll = self.query_one("#messages-scroll", VerticalScroll)
        for i, msg in enumerate(messages):
            bubble = MessageBubble(msg)
            if scroll.children:
                scroll.mount(bubble, before=scroll.children[0])
            else:
                scroll.mount(bubble)

    def update_message(self, msg: MessageModel) -> None:
        for i, existing in enumerate(self._messages):
            if existing.id == msg.id:
                self._messages[i] = msg
                break
        self.set_messages(self._messages)

    def remove_messages(self, message_ids: list[int]) -> None:
        self._messages = [m for m in self._messages if m.id not in message_ids]
        self.set_messages(self._messages)

    def _scroll_to_bottom(self) -> None:
        try:
            scroll = self.query_one("#messages-scroll", VerticalScroll)
            scroll.scroll_end(animate=False)
        except Exception:
            pass
