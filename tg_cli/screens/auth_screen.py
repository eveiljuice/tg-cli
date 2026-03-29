"""Authentication screen: phone -> code -> 2FA."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, LoadingIndicator, Static

from tg_cli.config import save_credentials

if TYPE_CHECKING:
    from tg_cli.app import TgCliApp


class SetupScreen(Screen):
    """First-run screen for API credentials."""

    DEFAULT_CSS = """
    SetupScreen {
        align: center middle;
    }

    #setup-box {
        width: 60;
        max-height: 22;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #setup-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        width: 100%;
        padding: 1 0;
    }

    #setup-hint {
        color: $text-muted;
        padding: 0 0 1 0;
    }

    #setup-error {
        color: $error;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="setup-box"):
            yield Label("tg-cli Setup", id="setup-title")
            yield Static(
                "Get credentials at my.telegram.org\n"
                "(API development tools)",
                id="setup-hint",
            )
            yield Label("API ID:")
            yield Input(placeholder="12345678", id="api-id-input")
            yield Label("API Hash:")
            yield Input(placeholder="abcdef1234...", id="api-hash-input")
            yield Static("", id="setup-error")
            yield Button("Save & Continue", id="setup-save", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#api-id-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "setup-save":
            self._save()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "api-id-input":
            self.query_one("#api-hash-input", Input).focus()
        elif event.input.id == "api-hash-input":
            self._save()

    def _save(self) -> None:
        api_id_str = self.query_one("#api-id-input", Input).value.strip()
        api_hash = self.query_one("#api-hash-input", Input).value.strip()
        error_label = self.query_one("#setup-error", Static)

        if not api_id_str or not api_hash:
            error_label.update("Both fields are required.")
            return
        try:
            api_id = int(api_id_str)
        except ValueError:
            error_label.update("API ID must be a number.")
            return

        save_credentials(api_id, api_hash)
        app: TgCliApp = self.app  # type: ignore
        app.config.api_id = api_id
        app.config.api_hash = api_hash
        self.dismiss(True)


class AuthScreen(Screen):
    """Phone number / verification code / 2FA password entry."""

    BINDINGS = [("escape", "app.quit", "Quit")]

    DEFAULT_CSS = """
    AuthScreen {
        align: center middle;
    }

    #auth-box {
        width: 60;
        max-height: 20;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #auth-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        width: 100%;
        padding: 1 0;
    }

    #auth-error {
        color: $error;
    }

    #auth-status {
        color: $text-muted;
        text-align: center;
    }

    #auth-loading {
        height: 1;
        display: none;
    }

    #auth-loading.visible {
        display: block;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._step = "phone"  # phone | code | 2fa

    def compose(self) -> ComposeResult:
        with Vertical(id="auth-box"):
            yield Label("tg-cli Login", id="auth-title")
            yield Static("Enter your phone number (with country code):", id="auth-prompt")
            yield Input(placeholder="+1234567890", id="auth-input")
            yield Static("", id="auth-error")
            yield Static("", id="auth-status")
            yield LoadingIndicator(id="auth-loading")
            yield Button("Send Code", id="auth-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#auth-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "auth-submit":
            self._handle_submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._handle_submit()

    def _handle_submit(self) -> None:
        value = self.query_one("#auth-input", Input).value.strip()
        if not value:
            return

        self.query_one("#auth-error", Static).update("")
        self._set_loading(True)

        if self._step == "phone":
            self._set_status("Sending verification code...")
            self._do_send_code(value)
        elif self._step == "code":
            self._set_status("Verifying code...")
            self._do_sign_in(value)
        elif self._step == "2fa":
            self._set_status("Checking password...")
            self._do_2fa(value)

    def _set_loading(self, loading: bool) -> None:
        """Show/hide loading indicator and disable/enable input."""
        btn = self.query_one("#auth-submit", Button)
        inp = self.query_one("#auth-input", Input)
        indicator = self.query_one("#auth-loading", LoadingIndicator)

        btn.disabled = loading
        inp.disabled = loading

        if loading:
            indicator.add_class("visible")
        else:
            indicator.remove_class("visible")
            self._set_status("")

    def _set_status(self, text: str) -> None:
        self.query_one("#auth-status", Static).update(text)

    @work(exclusive=True, thread=True)
    def _do_send_code(self, phone: str) -> None:
        app: TgCliApp = self.app  # type: ignore
        error = app.auth_flow.send_code(phone)
        if error:
            app.call_from_thread(self._on_error, error)
        else:
            app.call_from_thread(self._on_code_sent)

    def _on_code_sent(self) -> None:
        self._set_loading(False)
        self._step = "code"
        self.query_one("#auth-prompt", Static).update(
            "Enter the verification code from Telegram:"
        )
        inp = self.query_one("#auth-input", Input)
        inp.value = ""
        inp.placeholder = "12345"
        inp.disabled = False
        self.query_one("#auth-submit", Button).label = "Sign In"
        self.notify(
            "Verification code sent! Check your Telegram app.",
            title="Code Sent",
            severity="information",
            timeout=8,
        )
        inp.focus()

    @work(exclusive=True, thread=True)
    def _do_sign_in(self, code: str) -> None:
        app: TgCliApp = self.app  # type: ignore
        result = app.auth_flow.sign_in(code)
        if result is None:
            app.auth_flow.setup_handlers()
            app.call_from_thread(self.dismiss, True)
        elif result == "2fa":
            app.call_from_thread(self._on_2fa_needed)
        else:
            app.call_from_thread(self._on_error, result)

    def _on_2fa_needed(self) -> None:
        self._set_loading(False)
        self._step = "2fa"
        self.query_one("#auth-prompt", Static).update(
            "Enter your two-factor authentication password:"
        )
        inp = self.query_one("#auth-input", Input)
        inp.value = ""
        inp.placeholder = "Password"
        inp.password = True
        inp.disabled = False
        self.query_one("#auth-submit", Button).label = "Submit"
        self.notify(
            "Two-factor authentication required.",
            title="2FA",
            severity="warning",
            timeout=5,
        )
        inp.focus()

    @work(exclusive=True, thread=True)
    def _do_2fa(self, password: str) -> None:
        app: TgCliApp = self.app  # type: ignore
        result = app.auth_flow.sign_in_2fa(password)
        if result is None:
            app.auth_flow.setup_handlers()
            app.call_from_thread(self.dismiss, True)
        else:
            app.call_from_thread(self._on_error, result)

    def _on_error(self, msg: str) -> None:
        self._set_loading(False)
        self.query_one("#auth-error", Static).update(msg)
        self.query_one("#auth-input", Input).disabled = False
        self.query_one("#auth-input", Input).focus()
        self.notify(msg, title="Error", severity="error", timeout=8)
