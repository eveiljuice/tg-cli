"""TelegramBridge: integration layer between Telethon and Textual."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING, Any

from telethon import TelegramClient, events
from telethon.tl.types import (
    Channel,
    Chat,
    User,
    MessageMediaDocument,
    MessageMediaPhoto,
)

from tg_cli.config import Config
from tg_cli.messages import (
    AuthComplete,
    AuthRequired,
    NewTelegramMessage,
    MessageDeleted,
    MessageEdited as MessageEditedMsg,
)
from tg_cli.models.dialog import DialogModel
from tg_cli.models.message import MessageModel

if TYPE_CHECKING:
    from tg_cli.app import TgCliApp

log = logging.getLogger(__name__)


class TelegramBridge:
    """Runs Telethon in a dedicated background thread with its own event loop."""

    def __init__(self, app: TgCliApp, config: Config) -> None:
        self.app = app
        self.config = config
        self.loop: asyncio.AbstractEventLoop | None = None
        self.client: TelegramClient | None = None
        self.me: User | None = None
        self._entity_cache: dict[int, Any] = {}
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._keep_alive = threading.Event()

    def start(self) -> None:
        """Start Telethon in a background thread. Blocks until loop is ready."""
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=30):
            raise RuntimeError("Telethon failed to start in 30s")

    def _thread_main(self) -> None:
        """Thread entry: create loop, connect, keep alive."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect_and_check())
            # Keep the loop running so we can submit coroutines to it
            self.loop.run_until_complete(self._stay_alive())
        except Exception as e:
            log.error("Telethon thread crashed: %s", e)
        finally:
            log.info("Telethon thread exiting")

    async def _connect_and_check(self) -> None:
        """Connect and check auth status. Does NOT start event loop yet."""
        self.client = TelegramClient(
            self.config.session_path,
            self.config.api_id,
            self.config.api_hash,
            connection_retries=3,
            auto_reconnect=True,
        )

        log.info("Connecting to Telegram...")
        await self.client.connect()
        log.info("Connected!")
        self._ready.set()

        authorized = await self.client.is_user_authorized()
        if not authorized:
            log.info("Not authorized, requesting login")
            self.app.post_message(AuthRequired())
        else:
            self.me = await self.client.get_me()
            log.info("Authorized as %s", getattr(self.me, "username", "?"))
            await self._setup_handlers()
            self.app.post_message(AuthComplete(user=self.me))

    async def _stay_alive(self) -> None:
        """Keep the event loop running for coroutine submissions."""
        # Wait until told to run_until_disconnected or stop
        while not self._keep_alive.is_set():
            await asyncio.sleep(0.1)
        # Now run the real event loop for receiving updates
        log.info("Starting Telethon event loop")
        await self.client.run_until_disconnected()

    def start_receiving(self) -> None:
        """Signal the bridge to start receiving updates (call after auth)."""
        self._keep_alive.set()

    def run_sync(self, coro: Any, timeout: float = 60) -> Any:
        """Run a coroutine on Telethon's loop from any thread. Blocking."""
        if self.loop is None or self.loop.is_closed():
            raise RuntimeError("Telethon loop not running")
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=timeout)

    def disconnect(self) -> None:
        if self.client and self.loop and not self.loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.client.disconnect(), self.loop
                )
                future.result(timeout=5)
            except Exception:
                pass

    # --- Event handlers ---

    async def _setup_handlers(self) -> None:
        self.client.add_event_handler(self._on_new_message, events.NewMessage)
        self.client.add_event_handler(self._on_message_edited, events.MessageEdited)
        self.client.add_event_handler(self._on_message_deleted, events.MessageDeleted)

    async def _on_new_message(self, event: events.NewMessage.Event) -> None:
        msg = await self._convert_message(event.message)
        chat_id = event.chat_id or 0
        self.app.post_message(NewTelegramMessage(message=msg, chat_id=chat_id))

    async def _on_message_edited(self, event: events.MessageEdited.Event) -> None:
        msg = await self._convert_message(event.message)
        chat_id = event.chat_id or 0
        self.app.post_message(MessageEditedMsg(message=msg, chat_id=chat_id))

    async def _on_message_deleted(self, event: events.MessageDeleted.Event) -> None:
        chat_id = event.chat_id or 0
        self.app.post_message(
            MessageDeleted(message_ids=list(event.deleted_ids), chat_id=chat_id)
        )

    # --- API methods ---

    async def fetch_dialogs(self, limit: int = 100) -> list[DialogModel]:
        dialogs = []
        async for d in self.client.iter_dialogs(limit=limit):
            entity = d.entity
            is_group = isinstance(entity, (Chat, Channel)) and (
                not getattr(entity, "broadcast", False)
            )
            is_channel = isinstance(entity, Channel) and getattr(
                entity, "broadcast", False
            )
            is_user = isinstance(entity, User)

            last_text = ""
            last_date = None
            if d.message:
                last_text = d.message.text or ""
                if not last_text and d.message.media:
                    last_text = _media_type_label(d.message.media)
                last_date = d.message.date

            self._entity_cache[d.id] = entity

            dialogs.append(
                DialogModel(
                    id=d.id,
                    name=d.name or "",
                    unread_count=d.unread_count,
                    last_message_text=last_text,
                    last_message_date=last_date,
                    is_group=is_group,
                    is_channel=is_channel,
                    is_user=is_user,
                    entity=entity,
                )
            )
        return dialogs

    async def fetch_messages(
        self, chat_id: int, limit: int = 50, offset_id: int = 0
    ) -> list[MessageModel]:
        entity = self._entity_cache.get(chat_id)
        if entity is None:
            entity = await self.client.get_entity(chat_id)
            self._entity_cache[chat_id] = entity

        messages = []
        async for msg in self.client.iter_messages(
            entity, limit=limit, offset_id=offset_id
        ):
            messages.append(await self._convert_message(msg))

        messages.reverse()
        return messages

    async def send_message(
        self, chat_id: int, text: str, reply_to: int | None = None,
    ) -> None:
        entity = self._entity_cache.get(chat_id)
        if entity is None:
            entity = await self.client.get_entity(chat_id)
            self._entity_cache[chat_id] = entity
        await self.client.send_message(entity, text, reply_to=reply_to)

    async def mark_read(self, chat_id: int) -> None:
        entity = self._entity_cache.get(chat_id)
        if entity is None:
            entity = await self.client.get_entity(chat_id)
        await self.client.send_read_acknowledge(entity)

    async def _convert_message(self, msg: Any) -> MessageModel:
        sender_name = ""
        if msg.sender:
            if isinstance(msg.sender, User):
                parts = [msg.sender.first_name or "", msg.sender.last_name or ""]
                sender_name = " ".join(p for p in parts if p)
            else:
                sender_name = getattr(msg.sender, "title", "") or ""

        media_type = None
        media_file_name = None
        if msg.media:
            media_type = _media_type_label(msg.media)
            if hasattr(msg.media, "document") and msg.media.document:
                for attr in msg.media.document.attributes:
                    if hasattr(attr, "file_name"):
                        media_file_name = attr.file_name
                        break

        return MessageModel(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=sender_name,
            text=msg.text or "",
            date=msg.date,
            is_outgoing=getattr(msg, "out", False),
            reply_to_msg_id=msg.reply_to.reply_to_msg_id if msg.reply_to else None,
            media_type=media_type,
            media_file_name=media_file_name,
            raw=msg,
        )


def _media_type_label(media: Any) -> str:
    if isinstance(media, MessageMediaPhoto):
        return "photo"
    if isinstance(media, MessageMediaDocument):
        doc = media.document
        if doc:
            for attr in doc.attributes:
                cls_name = type(attr).__name__
                if "Sticker" in cls_name:
                    return "sticker"
                if "Video" in cls_name:
                    return "video"
                if "Audio" in cls_name:
                    return "audio"
                if "Voice" in cls_name:
                    return "voice"
        return "document"
    return "media"
