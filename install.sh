#!/usr/bin/env bash
set -euo pipefail

echo "Installing tg-cli..."

if command -v pipx &>/dev/null; then
    echo "Using pipx..."
    pipx install git+https://github.com/eveiljuice/tg-cli.git
elif command -v pip &>/dev/null; then
    echo "Using pip..."
    pip install git+https://github.com/eveiljuice/tg-cli.git
elif command -v pip3 &>/dev/null; then
    echo "Using pip3..."
    pip3 install git+https://github.com/eveiljuice/tg-cli.git
else
    echo "Error: pip not found. Install Python 3.11+ first."
    exit 1
fi

echo ""
echo "Done! Run 'tg-cli' to start."
echo "You'll need API credentials from https://my.telegram.org"
