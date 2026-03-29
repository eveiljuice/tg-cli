"""Splash screen with animated Telegram logo."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

LOGO_TEXT = (
    " [bold #2AABEE]████████╗[/][bold #FFFFFF]  ██████╗ [/]\n"
    " [bold #2AABEE]╚══██╔══╝[/][bold #FFFFFF] ██╔════╝ [/]\n"
    " [bold #2AABEE]   ██║   [/][bold #FFFFFF] ██║  ███╗[/]\n"
    " [bold #2AABEE]   ██║   [/][bold #FFFFFF] ██║   ██║[/]\n"
    " [bold #2AABEE]   ██║   [/][bold #FFFFFF] ╚██████╔╝[/]\n"
    " [bold #2AABEE]   ╚═╝   [/][bold #FFFFFF]  ╚═════╝ [/]"
)

TITLE = "[bold #2AABEE]t[/][bold #FFFFFF]g[/][dim]-cli[/]"


class SplashLogo(Widget):
    """Startup splash with logo and progress."""

    DEFAULT_CSS = """
    SplashLogo {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }
    """

    progress: reactive[float] = reactive(0.0)
    status_text: reactive[str] = reactive("Connecting...")

    def render(self) -> str:
        bar_width = 30
        filled = int(self.progress * bar_width)
        empty = bar_width - filled
        pct = int(self.progress * 100)

        bar = f"[#2AABEE]{'━' * filled}[/][#333333]{'━' * empty}[/] [bold #2AABEE]{pct}%[/]"

        return (
            f"{LOGO_TEXT}\n"
            f"\n"
            f"{TITLE}\n"
            f"\n"
            f"{bar}\n"
            f"\n"
            f"[#888888]{self.status_text}[/]"
        )
