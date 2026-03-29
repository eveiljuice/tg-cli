# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

tg-cli is a full-featured Telegram client for the terminal, built with Python + Telethon (MTProto) + Textual (TUI).

## Commands

```bash
# Install (editable)
pip install -e .

# Run
python -m tg_cli
# or after install:
tg-cli

# Config lives at ~/.tg-cli/ (config.toml, session.session, downloads/)
# API credentials: .env file (API_ID, API_HASH) or first-run setup screen
```

No test suite yet. No linter configured.

## Architecture

### Two-thread model

Telethon and Textual each need their own async event loop. They run on **separate threads**:

- **Main thread**: Textual event loop (`App.run()`)
- **Daemon thread**: Telethon event loop (`TelegramBridge._thread_main()` → `asyncio.new_event_loop()`)

### Bridge pattern (`tg_cli/telegram/client.py`)

`TelegramBridge` is the integration layer. Two critical methods:

- **`run_sync(coro, timeout)`** — submits a coroutine to Telethon's loop via `run_coroutine_threadsafe`, blocks calling thread. Used by all `@work(thread=True)` workers in screens.
- **`app.post_message()`** — thread-safe Textual method. Used by Telethon event handlers to push updates to the UI.

### Startup sequence

1. `TgCliApp.on_mount()` → checks credentials → `SetupScreen` if missing
2. `_connect_telegram()` `@work(thread=True)` → `bridge.start()` → spawns Telethon thread, connects, checks auth
3. Telethon posts `AuthRequired` or `AuthComplete` → app pushes `AuthScreen` or `MainScreen`
4. After auth: `bridge.start_receiving()` flips a flag → Telethon enters `run_until_disconnected()`

### Worker pattern

All Telegram API calls from Textual use `@work(thread=True)` workers that call `bridge.run_sync()`. This keeps the Textual main loop unblocked. UI updates from workers use `app.call_from_thread()`. **`Screen` objects do NOT have `call_from_thread`** — always use `app.call_from_thread()`.

### Event flow

Incoming: Telethon handler → `app.post_message(NewTelegramMessage)` → `MainScreen.on_new_telegram_message()` → widget update

Outgoing: `MessageInput.Submitted` → `MainScreen._send_message()` `@work` → `bridge.run_sync(bridge.send_message())`

### Key constraint

`run_until_disconnected()` must only be called AFTER authorization completes. Before auth, the Telethon thread stays alive via a polling `_stay_alive()` loop that checks a `threading.Event`.

## Module map

- `tg_cli/telegram/client.py` — `TelegramBridge`: Telethon lifecycle, `run_sync`, event handlers, API wrappers
- `tg_cli/telegram/auth.py` — `AuthFlow`: synchronous wrappers over `send_code_request`/`sign_in`/2FA (calls `run_sync` internally)
- `tg_cli/app.py` — `TgCliApp`: screen management, splash → auth → main transitions
- `tg_cli/screens/main_screen.py` — grid layout, routes all Telegram messages to widgets
- `tg_cli/messages.py` — all custom `Message` subclasses (the event bus between bridge and UI)
- `tg_cli/models/` — pure dataclasses (`DialogModel`, `MessageModel`), no framework deps
- `tg_cli/widgets/splash.py` — animated pixel-art logo with progress bar
