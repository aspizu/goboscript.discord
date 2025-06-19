from __future__ import annotations

import logging
import re
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import TYPE_CHECKING

from discord import File

from . import scratch
from .misc import sh, zip_directory_contents

if TYPE_CHECKING:
    from discord import Message

logger = logging.getLogger()
PROJECT_URL_RE = re.compile(r"https?://scratch\.mit\.edu/projects/(\d+)/?")
MSG = """
Here is your Scratch project converted to goboscript.
-# Powered by <https://github.com/aspizu/sb2gs>
"""[1:-1]


async def on_message(message: Message) -> bool:
    match = PROJECT_URL_RE.search(message.content)
    project_id = match and match.group(1)
    attachment = next(iter(message.attachments), None)
    if project_id:
        title = (await scratch.get_project(project_id))["title"]
        logger.info("sb2gs from scratch %s", project_id)
    elif attachment:
        title = attachment.filename.removesuffix(".sb3")
        logger.info("sb2gs from attachment %s", title)
    else:
        return False
    with (
        NamedTemporaryFile(suffix=".sb3") as sb3_file,
        TemporaryDirectory() as temp_dir,
        NamedTemporaryFile(suffix=".zip") as zip_file,
    ):
        if project_id:
            await scratch.download_project_sb3(project_id, sb3_file.name)
        if attachment:
            await attachment.save(Path(sb3_file.name))
        await sh(
            "uv",
            "run",
            "python",
            "-m",
            "sb2gs",
            "--input",
            sb3_file.name,
            "--output",
            temp_dir,
        )
        zip_directory_contents(temp_dir, zip_file.name)
        file = File(zip_file.name, f"{title}.zip")
        await message.reply(MSG, file=file)
    return True
