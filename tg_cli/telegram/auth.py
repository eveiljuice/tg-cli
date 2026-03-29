"""Authentication flow for Telegram."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    FloodWaitError,
)

if TYPE_CHECKING:
    from tg_cli.telegram.client import TelegramBridge

log = logging.getLogger(__name__)


class AuthFlow:
    def __init__(self, bridge: TelegramBridge) -> None:
        self.bridge = bridge
        self._phone: str = ""
        self._phone_code_hash: str = ""

    def send_code(self, phone: str) -> str | None:
        """Send verification code. Returns None on success, error string on failure."""
        self._phone = phone
        try:
            result = self.bridge.run_sync(
                self.bridge.client.send_code_request(phone)
            )
            self._phone_code_hash = result.phone_code_hash
            return None
        except FloodWaitError as e:
            return f"Too many requests. Wait {e.seconds} seconds."
        except Exception as e:
            log.error("send_code error: %s", e)
            return str(e)

    def sign_in(self, code: str) -> str | None:
        """Sign in with code. Returns None=success, '2fa'=need 2FA, else error."""
        try:
            self.bridge.run_sync(
                self.bridge.client.sign_in(
                    self._phone, code, phone_code_hash=self._phone_code_hash
                )
            )
            self.bridge.me = self.bridge.run_sync(self.bridge.client.get_me())
            return None
        except SessionPasswordNeededError:
            return "2fa"
        except PhoneCodeInvalidError:
            return "Invalid code. Try again."
        except PhoneCodeExpiredError:
            return "Code expired. Request a new one."
        except FloodWaitError as e:
            return f"Too many attempts. Wait {e.seconds} seconds."
        except Exception as e:
            log.error("sign_in error: %s", e)
            return str(e)

    def sign_in_2fa(self, password: str) -> str | None:
        """Complete 2FA. Returns None on success, error string on failure."""
        try:
            self.bridge.run_sync(self.bridge.client.sign_in(password=password))
            self.bridge.me = self.bridge.run_sync(self.bridge.client.get_me())
            return None
        except PasswordHashInvalidError:
            return "Wrong password. Try again."
        except FloodWaitError as e:
            return f"Too many attempts. Wait {e.seconds} seconds."
        except Exception as e:
            log.error("2fa error: %s", e)
            return str(e)

    def setup_handlers(self) -> None:
        """Set up Telethon event handlers after auth."""
        self.bridge.run_sync(self.bridge._setup_handlers())
