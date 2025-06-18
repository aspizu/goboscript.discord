from __future__ import annotations

import os

import anthropic
import google.genai
import voyageai
from dotenv import load_dotenv
from redisvl.index import AsyncSearchIndex
from redisvl.schema import IndexSchema
from redisvl.types import AsyncRedis

# -- from redisvl.utils.vectorize.text.huggingface import HFTextVectorizer

load_dotenv()

# -- vectorizer = HFTextVectorizer(model="Qwen/Qwen3-Embedding-0.6B", device="cpu")
vo_client = voyageai.AsyncClient()
google_client = google.genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
redis_client = AsyncRedis.from_url("redis://localhost:6379")
schema = IndexSchema.from_yaml("schema.yml")
index = AsyncSearchIndex.from_dict(
    schema.to_dict(),
    redis_client=redis_client,
    validate_on_load=True,
)
ant_client = anthropic.AsyncAnthropic()
