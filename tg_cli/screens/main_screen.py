"""Main chat screen — the primary interface after authentication."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen

from tg_cli.messages import (
    NewTelegramMessage,
    MessageEdited,
    MessageDeleted,
)
from tg_cli.widgets.chat_list import ChatList
from tg_cli.widgets.message_input import MessageInput
from tg_cli.widgets.message_view import MessageView
from tg_cli.widgets.status_bar import StatusBar

if TYPE_CHECKING:
    from tg_cli.app import TgCliApp

log = logging.getLogger(__name__)


class MainScreen(Screen):
    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Quit"),
        Binding("tab", "focus_next", "Next panel"),
        Binding("shift+tab", "focus_previous", "Previous panel"),
        Binding("ctrl+s", "search", "Search chats"),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }

    #main-body {
        height: 1fr;
    }

    #sidebar {
        width: 32;
        border-right: solid $primary;
    }

    #chat-area {
        width: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_chat_id: int | None = None

    def compose(self) -> ComposeResult:
        yield StatusBar()
        with Horizontal(id="main-body"):
            with Vertical(id="sidebar"):
                yield ChatList()
            with Vertical(id="chat-area"):
                yield MessageView()
                yield MessageInput()

    def on_mount(self) -> None:
        log.info("MainScreen mounted, loading dialogs...")
        self._load_dialogs()

    @work(exclusive=True, group="dialogs", thread=True)
    def _load_dialogs(self) -> None:
        app: TgCliApp = self.app  # type: ignore
        bridge = app.bridge
        if not bridge:
            return
        try:
            log.info("Fetching dialogs...")
            dialogs = bridge.run_sync(bridge.fetch_dialogs())
            log.info("Got %d dialogs", len(dialogs))
            # Use call_from_thread to directly update the widget
            app.call_from_thread(self._apply_dialogs, dialogs)
        except Exception as e:
            log.error("Failed to load dialogs: %s", e, exc_info=True)
            app.call_from_thread(
                self.app.notify, f"Failed to load chats: {e}", severity="error"
            )

    def _apply_dialogs(self, dialogs: list) -> None:
        log.info("Applying %d dialogs to ChatList", len(dialogs))
        chat_list = self.query_one(ChatList)
        chat_list.set_dialogs(dialogs)

    def on_chat_list_chat_selected(self, event: ChatList.ChatSelected) -> None:
        self._current_chat_id = event.chat_id
        msg_view = self.query_one(MessageView)
        msg_view.clear_messages()
        msg_view.set_chat_name(event.chat_name)
        self._load_messages(event.chat_id)
        self._mark_read(event.chat_id)
        self.query_one(MessageInput).focus()

    @work(exclusive=True, group="messages", thread=True)
    def _load_messages(self, chat_id: int) -> None:
        app: TgCliApp = self.app  # type: ignore
        bridge = app.bridge
        if not bridge:
            return
        try:
            messages = bridge.run_sync(bridge.fetch_messages(chat_id))
            app.call_from_thread(self._apply_messages, messages, chat_id)
        except Exception as e:
            log.error("Failed to load messages: %s", e, exc_info=True)

    def _apply_messages(self, messages: list, chat_id: int) -> None:
        if chat_id != self._current_chat_id:
            return
        msg_view = self.query_one(MessageView)
        msg_view.set_messages(messages)

    @work(group="read", thread=True)
    def _mark_read(self, chat_id: int) -> None:
        app: TgCliApp = self.app  # type: ignore
        bridge = app.bridge
        if not bridge:
            return
        try:
            bridge.run_sync(bridge.mark_read(chat_id), timeout=10)
        except Exception:
            pass

    def on_new_telegram_message(self, event: NewTelegramMessage) -> None:
        if event.chat_id == self._current_chat_id:
            # Skip if outgoing (already shown instantly on send)
            if not event.message.is_outgoing:
                msg_view = self.query_one(MessageView)
                msg_view.append_message(event.message)
        self._load_dialogs()

    def on_message_edited(self, event: MessageEdited) -> None:
        if event.chat_id == self._current_chat_id:
            msg_view = self.query_one(MessageView)
            msg_view.update_message(event.message)

    def on_message_deleted(self, event: MessageDeleted) -> None:
        if event.chat_id == self._current_chat_id:
            msg_view = self.query_one(MessageView)
            msg_view.remove_messages(event.message_ids)

    def on_message_input_submitted(self, event: MessageInput.Submitted) -> None:
        if self._current_chat_id is None:
            return
        self._send_message(self._current_chat_id, event.text, event.reply_to)

    @work(group="send", thread=True)
    def _send_message(
        self, chat_id: int, text: str, reply_to: int | None
    ) -> None:
        from datetime import datetime, timezone
        from tg_cli.models.message import MessageModel

        app: TgCliApp = self.app  # type: ignore
        bridge = app.bridge
        if not bridge:
            return

        # Show message immediately in UI
        temp_msg = MessageModel(
            id=-1,
            sender_id=None,
            sender_name="You",
            text=text,
            date=datetime.now(timezone.utc),
            is_outgoing=True,
            reply_to_msg_id=reply_to,
            media_type=None,
            media_file_name=None,
            raw=None,
        )
        app.call_from_thread(self._show_sent_message, temp_msg, chat_id)

        try:
            bridge.run_sync(bridge.send_message(chat_id, text, reply_to=reply_to))
        except Exception as e:
            self.app.notify(f"Send failed: {e}", severity="error")

    def _show_sent_message(self, msg, chat_id: int) -> None:
        if chat_id == self._current_chat_id:
            msg_view = self.query_one(MessageView)
            msg_view.append_message(msg)

    def action_search(self) -> None:
        from tg_cli.screens.search_screen import SearchScreen
        self.app.push_screen(SearchScreen(), callback=lambda result: None)
