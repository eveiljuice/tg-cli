"""Main Textual application for tg-cli."""

from __future__ import annotations

import logging
import sys

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding

from tg_cli.config import Config, load_config, LOG_FILE
from tg_cli.messages import AuthComplete, AuthRequired
from tg_cli.telegram.auth import AuthFlow
from tg_cli.telegram.client import TelegramBridge
from tg_cli.widgets.splash import SplashLogo

log = logging.getLogger("tg_cli")


def setup_logging() -> None:
    """Set up file logging before anything else."""
    handler = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    )
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class TgCliApp(App):
    TITLE = "tg-cli"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(self) -> None:
        setup_logging()
        super().__init__()
        self.config: Config = load_config()
        self.bridge: TelegramBridge | None = None
        self.auth_flow: AuthFlow | None = None

    def compose(self) -> ComposeResult:
        yield SplashLogo()

    def on_mount(self) -> None:
        if not self.config.api_id or not self.config.api_hash:
            self._show_setup()
        else:
            self._start_telegram()

    def _update_splash(self, progress: float, status: str) -> None:
        try:
            splash = self.query_one(SplashLogo)
            splash.progress = progress
            splash.status_text = status
        except Exception:
            pass

    def _show_setup(self) -> None:
        from tg_cli.screens.auth_screen import SetupScreen

        def on_setup_done(result: bool | None) -> None:
            if result:
                self._start_telegram()
            else:
                self.exit()

        self.push_screen(SetupScreen(), callback=on_setup_done)

    def _start_telegram(self) -> None:
        self._update_splash(0.1, "Initializing...")
        self.bridge = TelegramBridge(self, self.config)
        self.auth_flow = AuthFlow(self.bridge)
        self._connect_telegram()

    @work(exclusive=True, group="telegram", thread=True)
    def _connect_telegram(self) -> None:
        try:
            self.app.call_from_thread(self._update_splash, 0.3, "Connecting to Telegram...")
            self.bridge.start()
            self.app.call_from_thread(self._update_splash, 0.8, "Connected!")
        except Exception as e:
            log.error("Connect failed: %s", e)
            self.app.call_from_thread(
                self._update_splash, 0.0, f"Connection failed: {e}"
            )

    def on_auth_required(self, event: AuthRequired) -> None:
        self._update_splash(1.0, "Login required")
        from tg_cli.screens.auth_screen import AuthScreen

        def on_auth_done(result: bool | None) -> None:
            if result:
                self._on_authenticated()
            else:
                self.exit()

        self.set_timer(0.5, lambda: self.push_screen(AuthScreen(), callback=on_auth_done))

    def on_auth_complete(self, event: AuthComplete) -> None:
        name = getattr(event.user, "first_name", "") or "user"
        self._update_splash(1.0, f"Welcome, {name}!")
        self.set_timer(1.0, self._on_authenticated)

    def _on_authenticated(self) -> None:
        from tg_cli.screens.main_screen import MainScreen

        if self.bridge:
            self.bridge.start_receiving()

        self.push_screen(MainScreen())

        def update_bar() -> None:
            from tg_cli.widgets.status_bar import StatusBar
            try:
                sb = self.screen.query_one(StatusBar)
                sb.connected = True
                if self.bridge and self.bridge.me:
                    sb.username = self.bridge.me.username or ""
            except Exception:
                pass

        self.set_timer(0.5, update_bar)
