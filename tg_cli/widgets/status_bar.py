"""Status bar widget — connection status, user info."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        width: 100%;
        background: #1a1a2e;
        color: #e0e0e0;
        padding: 0 1;
    }
    """

    connected: reactive[bool] = reactive(False)
    username: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Static("", id="status-text")

    def watch_connected(self) -> None:
        self._update()

    def watch_username(self) -> None:
        self._update()

    def _update(self) -> None:
        indicator = "[green]●[/]" if self.connected else "[red]●[/]"
        status = "Connected" if self.connected else "Disconnected"
        user = f" | @{self.username}" if self.username else ""
        text = f" {indicator} {status}{user}  |  Tab: switch panels  Ctrl+S: search  Ctrl+Q: quit"
        try:
            self.query_one("#status-text", Static).update(text)
        except Exception:
            pass
