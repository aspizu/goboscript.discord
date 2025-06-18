from __future__ import annotations

import asyncio

import discord

from gbot import rag, sb2gs
from gbot.markdown_chunker import markdown_chunker

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return
    if bot.user not in message.mentions:
        return
    if any(file.filename.endswith(".sb3") for file in message.attachments):
        async with message.channel.typing():
            files = await asyncio.gather(*map(sb2gs.sb2gs, message.attachments))
        await message.reply(
            "Here are your Scratch projects converted to goboscript using <https://github.com/aspizu/sb2gs>"
            if len(files) > 1
            else "Here is your Scratch project converted to goboscript using <https://github.com/aspizu/sb2gs>",
            files=files,
        )
        return
    async with message.channel.typing():
        output = await rag.generate_response(message.content)
    if len(output) > 2000:  # noqa: PLR2004
        chunks = iter(markdown_chunker.split(output))
        await message.reply(next(chunks))
        for chunk in chunks:
            await message.channel.send(chunk)
    else:
        await message.reply(output)
