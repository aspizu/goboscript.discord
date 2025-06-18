from __future__ import annotations

import numpy as np

from . import vo_client


async def embed(
    documents: list[str],
) -> list[bytes]:
    response = await vo_client.embed(
        documents,
        model="voyage-3.5",
        input_type="query",
        output_dtype="float",
        output_dimension=1024,
    )
    return [np.array(i, dtype=np.float32).tobytes() for i in response.embeddings]
