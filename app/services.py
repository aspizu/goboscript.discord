from __future__ import annotations

import os

import httpx
from anthropic import AsyncClient as AnthropicAsyncClient
from redisvl.types import AsyncRedis
from voyageai.client_async import AsyncClient as VoyageAsyncClient

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

http = httpx.AsyncClient()
anthropic = AnthropicAsyncClient()
redis_client = AsyncRedis.from_url("redis://localhost:6379")
voyage = VoyageAsyncClient()
