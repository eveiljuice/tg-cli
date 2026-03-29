# tg-cli

Full-featured Telegram client for the terminal, built with Python + [Telethon](https://github.com/LonamiWebs/Telethon) + [Textual](https://github.com/Textualize/textual).

## Installation

### pip (recommended)

```bash
pip install git+https://github.com/eveiljuice/tg-cli.git
```

### curl + pip (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/eveiljuice/tg-cli/master/install.sh | bash
```

### pipx (isolated install)

```bash
pipx install git+https://github.com/eveiljuice/tg-cli.git
```

### From source

```bash
git clone https://github.com/eveiljuice/tg-cli.git
cd tg-cli
pip install .
```

## Getting Telegram API Credentials

Before using tg-cli, you need `api_id` and `api_hash` from Telegram:

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click **API development tools**
4. Fill in the form (app title: `tg-cli`, platform: Desktop)
5. Click **Create application**
6. Copy your `api_id` and `api_hash`

## Configuration

Set credentials via environment variables:

```bash
export API_ID=12345678
export API_HASH=abcdef1234567890
```

Or create a `.env` file:

```
API_ID=12345678
API_HASH=abcdef1234567890
```

Or just run `tg-cli` — it will prompt on first launch and save to `~/.tg-cli/config.toml`.

## Usage

```bash
tg-cli
```

### Key Bindings

| Key | Action |
|-----|--------|
| `Tab` | Switch between panels |
| `Enter` | Select chat / Send message |
| `Ctrl+S` | Search chats |
| `Ctrl+Q` | Quit |
| `PgUp/PgDn` | Scroll messages |

## Requirements

- Python 3.11+

## License

MIT
