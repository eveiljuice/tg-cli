"""Search screen — modal dialog for searching chats."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListView, ListItem, Static

if TYPE_CHECKING:
    from tg_cli.app import TgCliApp
    from tg_cli.models.dialog import DialogModel


class SearchScreen(ModalScreen[int | None]):
    """Modal search overlay for filtering chats."""

    BINDINGS = [("escape", "cancel", "Close")]

    CSS = """
    SearchScreen {
        align: center middle;
    }

    #search-container {
        width: 60;
        height: 20;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._dialogs: list[DialogModel] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="search-container"):
            yield Label("Search Chats")
            yield Input(placeholder="Type to search...", id="search-input")
            yield ListView(id="search-results")

    def on_mount(self) -> None:
        app: TgCliApp = self.app  # type: ignore
        if hasattr(app, "bridge") and app.bridge:
            # Use cached dialogs from the chat list
            from tg_cli.widgets.chat_list import ChatList

            try:
                chat_list = app.screen.query_one(ChatList)
                self._dialogs = list(chat_list._dialogs)
                self._update_results("")
            except Exception:
                pass
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_results(event.value)

    def _update_results(self, query: str) -> None:
        results = self.query_one("#search-results", ListView)
        results.clear()
        query_lower = query.lower()
        for dialog in self._dialogs:
            if query_lower and query_lower not in dialog.name.lower():
                continue
            item = ListItem(
                Static(f"{dialog.icon} {dialog.display_name}"),
                id=f"search-{dialog.id}",
            )
            item._dialog_id = dialog.id  # type: ignore
            results.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        dialog_id = getattr(event.item, "_dialog_id", None)
        self.dismiss(dialog_id)

    def action_cancel(self) -> None:
        self.dismiss(None)
