"""Chat list widget — left panel showing dialogs."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Static

from tg_cli.models.dialog import DialogModel

log = logging.getLogger(__name__)


class ChatListItem(ListItem):
    """A single chat entry in the list."""

    DEFAULT_CSS = """
    ChatListItem {
        height: 3;
        padding: 0 1;
    }

    ChatListItem:hover {
        background: $boost;
    }

    ChatListItem.-highlight {
        background: $accent;
    }
    """

    def __init__(self, dialog: DialogModel) -> None:
        self.dialog = dialog
        super().__init__()

    def compose(self) -> ComposeResult:
        d = self.dialog
        unread = f" [bold yellow]({d.unread_count})[/]" if d.unread_count > 0 else ""
        time_str = ""
        if d.last_message_date:
            local = d.last_message_date.astimezone(tz=None) if d.last_message_date.tzinfo else d.last_message_date
            time_str = local.strftime("%H:%M")

        name_line = f"{d.icon}[bold]{d.display_name}[/]{unread}"
        if time_str:
            name_line = f"{name_line}  [dim]{time_str}[/]"

        preview = f"  [dim]{d.last_message_preview}[/]" if d.last_message_preview else ""

        yield Static(f"{name_line}\n{preview}")


class ChatList(Widget, can_focus=True):
    DEFAULT_CSS = """
    ChatList {
        height: 1fr;
        width: 100%;
    }

    ChatList ListView {
        height: 1fr;
    }

    #chat-list-empty {
        height: 1fr;
        width: 100%;
        content-align: center middle;
        color: $text-muted;
    }
    """

    class ChatSelected(Message):
        def __init__(self, chat_id: int, chat_name: str) -> None:
            self.chat_id = chat_id
            self.chat_name = chat_name
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self._dialogs: list[DialogModel] = []

    def compose(self) -> ComposeResult:
        yield Static("Loading chats...", id="chat-list-empty")
        yield ListView(id="dialog-list")

    def set_dialogs(self, dialogs: list[DialogModel]) -> None:
        log.info("Setting %d dialogs in ChatList", len(dialogs))
        self._dialogs = dialogs

        # Hide empty label, show list
        try:
            self.query_one("#chat-list-empty", Static).display = False
        except Exception:
            pass

        lv = self.query_one("#dialog-list", ListView)
        lv.clear()

        for d in dialogs:
            item = ChatListItem(d)
            item._chat_id = d.id  # type: ignore
            item._chat_name = d.name  # type: ignore
            lv.append(item)

        lv.display = True

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        chat_id = getattr(event.item, "_chat_id", None)
        chat_name = getattr(event.item, "_chat_name", "")
        if chat_id is not None:
            self.post_message(self.ChatSelected(chat_id, chat_name))

    def select_by_id(self, chat_id: int) -> None:
        lv = self.query_one("#dialog-list", ListView)
        for i, item in enumerate(lv.children):
            if getattr(item, "_chat_id", None) == chat_id:
                lv.index = i
                chat_name = getattr(item, "_chat_name", "")
                self.post_message(self.ChatSelected(chat_id, chat_name))
                break
