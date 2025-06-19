from __future__ import annotations

import logging
import os

from rich.logging import RichHandler

LOG_FMT = "%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s"
LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def setup_logging() -> None:
    file_formatter = logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATE_FMT)
    file_handler = logging.FileHandler("log.txt")
    file_handler.setFormatter(file_formatter)
    logging.basicConfig(level=LOG_LEVEL, handlers=[RichHandler(), file_handler])
