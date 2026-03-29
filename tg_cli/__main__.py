"""Entry point for tg-cli: python -m tg_cli"""

from tg_cli.app import TgCliApp


def main() -> None:
    app = TgCliApp()
    app.run()


if __name__ == "__main__":
    main()
