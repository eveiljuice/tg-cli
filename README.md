# tg-cli

Full-featured Telegram client for the terminal.

## Getting Telegram API Credentials

Before using tg-cli, you need to obtain `api_id` and `api_hash` from Telegram:

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click on **API development tools**
4. Fill in the form:
   - **App title**: `tg-cli` (or any name)
   - **Short name**: `tgcli`
   - **Platform**: Desktop
   - **Description**: Terminal Telegram client
5. Click **Create application**
6. Copy your `api_id` (number) and `api_hash` (string)

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd tg-cli

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install
pip install -e .
```

## Configuration

Create a `.env` file in the project root:

```
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
```

Or the app will prompt you on first run and save to `~/.tg-cli/config.toml`.

## Usage

```bash
tg-cli
# or
python -m tg_cli
```

### Key Bindings

| Key | Action |
|-----|--------|
| `Tab` | Switch between panels |
| `Enter` | Select chat / Send message |
| `Ctrl+S` | Search chats |
| `Ctrl+R` | Reply to message |
| `Ctrl+E` | Edit message |
| `Ctrl+D` | Delete message |
| `Ctrl+Q` | Quit |
| `PgUp/PgDn` | Scroll messages |
