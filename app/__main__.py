from __future__ import annotations

from dotenv import load_dotenv

from ._logging import setup_logging

load_dotenv()
setup_logging()


if __name__ == "__main__":
    from .cli import cli

    cli()
