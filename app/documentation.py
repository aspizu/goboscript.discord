from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from langchain.text_splitter import RecursiveCharacterTextSplitter

if TYPE_CHECKING:
    from collections.abc import Generator

DOCS_PATH = Path("~/projects/goboscript/docs").expanduser()
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", " ", ""],
    keep_separator=True,
)


def get_documentation() -> Generator[tuple[str, str]]:
    for document in DOCS_PATH.glob("**/*.md"):
        for part in splitter.split_text(document.read_text()):
            yield document.relative_to(DOCS_PATH).as_posix(), part
