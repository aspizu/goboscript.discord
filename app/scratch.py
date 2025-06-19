from __future__ import annotations

import asyncio
import itertools
import json
import zipfile
from typing import Any

from .services import http


async def get_project(project_id: str) -> Any:
    res = await http.get(f"https://api.scratch.mit.edu/projects/{project_id}")
    return res.json()


async def get_project_json(project_id: str) -> bytes:
    token = (await get_project(project_id))["project_token"]
    res = await http.get(f"https://projects.scratch.mit.edu/{project_id}?token={token}")
    return res.content


async def get_asset(md5ext: str) -> bytes:
    res = await http.get(f"https://assets.scratch.mit.edu/{md5ext}")
    return res.content


async def download_project_sb3(project_id: str, path: str) -> None:
    project_json = await get_project_json(project_id)
    project = json.loads(project_json)
    costumes = itertools.chain(*(t["costumes"] for t in project["targets"]))

    async def map_asset(md5ext: str) -> tuple[str, bytes]:
        return (md5ext, await get_asset(md5ext))

    assets = await asyncio.gather(*map(map_asset, {c["md5ext"] for c in costumes}))
    with zipfile.ZipFile(path, "w") as zf:
        zf.open("project.json", "w").write(project_json)
        for md5ext, asset in assets:
            zf.open(md5ext, "w").write(asset)
