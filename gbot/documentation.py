from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from rich import print

if TYPE_CHECKING:
    from collections.abc import Generator


def get_documentation(
    root: str = "~/projects/goboscript/docs",
) -> Generator[tuple[str, str]]:
    root_path = Path(root).expanduser()
    for path in root_path.glob("**/*.md"):
        with path.open(encoding="utf-8") as file:
            markdown_text = file.read()
            for text in split_markdown_by_heading(markdown_text):
                yield (path.relative_to(root_path).as_posix(), text)


def split_markdown_by_heading(
    markdown_text: str, heading_level: int = 1
) -> Generator[str]:
    md = MarkdownIt()
    tokens = md.parse(markdown_text)

    current_chunk = []
    current_heading = False

    for token in tokens:
        if token.type == "heading_open":
            level = int(token.tag[1])
            if level == heading_level:
                if current_chunk:
                    yield "".join(current_chunk)
                    current_chunk = []
                current_heading = True

        if current_heading or current_chunk:
            current_chunk.append(
                token.content
                if token.type.endswith("_open") or token.type.endswith("_close")
                else token.markup + token.content + "\n"
            )
            if current_heading and token.type == "heading_close":
                current_heading = False

    if current_chunk:
        yield "".join(current_chunk)


if __name__ == "__main__":
    print(next(get_documentation()))
