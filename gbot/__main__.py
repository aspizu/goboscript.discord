from __future__ import annotations

import asyncio
import itertools
import os

import click

from gbot.embedding import embed

from . import documentation, index
from .bot import bot

BATCH_SIZE = 10


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--overwrite", default=False)
def create_index(overwrite: bool) -> None:
    async def _create_index() -> None:
        await index.create(overwrite=overwrite)

    asyncio.run(_create_index())


@cli.command()
def create_documentation() -> None:
    async def _create_documentation() -> None:
        for batch in itertools.batched(
            documentation.get_documentation(),
            BATCH_SIZE,
            strict=False,
        ):
            embeddings = await embed([text for (_, text) in batch])
            await index.load(
                (
                    {"path": path, "text": text, "embedding": embedding}
                    for (path, text), embedding in zip(batch, embeddings, strict=False)
                )
            )

    asyncio.run(_create_documentation())


@cli.command()
def run() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token is None:
        msg = "Discord bot token is not set in .env or environment"
        raise ValueError(msg)
    bot.run(token)


if __name__ == "__main__":
    cli()
