from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path


async def sh(program: str, *args: str, cwd: str | None = None) -> None:
    proc = await asyncio.subprocess.create_subprocess_exec(program, *args, cwd=cwd)
    await proc.wait()


def zip_directory_contents(dirpath: str, zippath: str) -> None:
    with zipfile.ZipFile(zippath, "w", zipfile.ZIP_STORED) as zf:
        for file in Path(dirpath).rglob("*"):
            if file.is_file():
                rel = file.relative_to(dirpath)
                zf.write(file, rel.as_posix())
