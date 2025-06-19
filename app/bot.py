from __future__ import annotations

import logging

from discord import Client, Intents, Message
from discord.channel import DMChannel

from . import rag, sb2gs

logger = logging.getLogger()
intents = Intents.default()
bot = Client(intents=intents)


@bot.event
async def on_message(message: Message) -> None:
    if message.author == bot.user:
        return
    if not (bot.user in message.mentions or isinstance(message.channel, DMChannel)):
        return
    async with message.channel.typing():
        if await sb2gs.on_message(message):
            return
        await rag.on_message(message)
