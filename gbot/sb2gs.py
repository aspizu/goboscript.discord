from __future__ import annotations

import shlex
import shutil
from asyncio import subprocess
from pathlib import Path

import discord

TEMP_SB3_FILE = Path("project.sb3")
TEMP_PROJECT_DIR = Path("project")
TEMP_ZIP_FILE = Path("project.zip")


class ConversionError(Exception):
    pass


async def run_command(command: str, *args: str, cwd: Path | str | None = None) -> int:
    proc = await subprocess.create_subprocess_exec(command, *args, cwd=cwd)
    await proc.wait()
    return proc.returncode or 0


async def sb2gs(attachment: discord.Attachment) -> discord.File:
    if not attachment.filename.endswith(".sb3"):
        msg = "File must have .sb3 extension"
        raise ConversionError(msg)

    TEMP_SB3_FILE.unlink(missing_ok=True)
    TEMP_ZIP_FILE.unlink(missing_ok=True)
    shutil.rmtree(TEMP_PROJECT_DIR, ignore_errors=True)

    await attachment.save(TEMP_SB3_FILE)

    exit_code = await run_command(
        "uv", *shlex.split("run python -m sb2gs --input project.sb3 --output project")
    )
    if exit_code != 0:
        msg = f"sb2gs conversion failed with exit code {exit_code}"
        raise ConversionError(msg)

    exit_code = await run_command(
        "zip",
        "-r",
        "../project.zip",
        ".",
        cwd=TEMP_PROJECT_DIR,
    )
    if exit_code != 0:
        msg = f"Zip creation failed with exit code {exit_code}"
        raise ConversionError(msg)

    if not TEMP_ZIP_FILE.exists():
        msg = "Zip file was not created successfully"
        raise ConversionError(msg)

    output_filename = attachment.filename.removesuffix(".sb3") + ".zip"
    return discord.File(str(TEMP_ZIP_FILE), output_filename)
