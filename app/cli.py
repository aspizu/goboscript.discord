from __future__ import annotations

import asyncio
import itertools
import logging
import os

import rich_click as click

from . import documentation, rag
from .bot import bot
from .embedding import embed

logger = logging.getLogger()
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


@click.group()
def cli() -> None: ...


@cli.command()
@click.option(
    "--overwrite",
    default=False,
    is_flag=True,
    help="Overwrite the existing index.",
)
def create_index(*, overwrite: bool) -> None:
    async def _create_index() -> None:
        await rag.index.create(overwrite=overwrite)

    asyncio.run(_create_index())


BATCH_SIZE = 10


@cli.command()
def create_documentation() -> None:
    async def _create_documentation() -> None:
        for batch in itertools.batched(
            documentation.get_documentation(), BATCH_SIZE, strict=False
        ):
            logger.info("batch")
            embeddings = await embed([text for (_, text) in batch])
            await asyncio.sleep(60)
            await rag.index.load(
                (
                    {"path": path, "text": text, "embedding": embedding}
                    for (path, text), embedding in zip(batch, embeddings, strict=False)
                )
            )

    asyncio.run(_create_documentation())


@cli.command()
def run() -> None:
    bot.run(token=DISCORD_BOT_TOKEN, log_handler=None)
