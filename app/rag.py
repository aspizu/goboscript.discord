from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import anthropic as anthropic_
import voyageai.error
from redisvl.index import AsyncSearchIndex
from redisvl.query import VectorQuery
from redisvl.schema import IndexSchema

from app.markdown_chunker import MarkdownChunker

from .embedding import embed
from .services import anthropic, redis_client

if TYPE_CHECKING:
    import anthropic.types as anthropic_types
    from discord import Message

schema = IndexSchema.from_yaml("schema.yml")
index = AsyncSearchIndex.from_dict(
    schema.to_dict(),
    redis_client=redis_client,
    validate_on_load=True,
)

REFERENCE_TEMPLATE = """
<reference>
<path>{path}</path>
<text>{text}</text>
</reference>
"""[1:-1]

QUERY_PROMPT_TEMPLATE = """
<references>
{references}
</references>
<user_query>
{user_query}
</user_query>
"""[1:-1]


def get_only_content(msg: anthropic_types.Message) -> str:
    assert len(msg.content) == 1
    assert msg.content[0].type == "text"
    return msg.content[0].text


async def generate_response(message: Message) -> None:
    embeddings = await embed([message.content])
    query = VectorQuery(
        vector=embeddings[0],
        vector_field_name="embedding",
        return_fields=["path", "text"],
        num_results=20,
    )
    results = await index.query(query)
    references = "\n".join(REFERENCE_TEMPLATE.format(**result) for result in results)
    msg = await anthropic.messages.create(
        messages=[{"role": "user", "content": message.content}],
        model="claude-3-5-haiku-20241022",
        max_tokens=1000,
        system=Path("prompts/request_type_prompt.txt").read_text(),
    )
    is_code_request = get_only_content(msg).strip().lower() == "true"
    if is_code_request:
        system = Path("prompts/rag_code_system_prompt.txt").read_text()
    else:
        system = Path("prompts/rag_system_prompt.txt").read_text()
    msg = await anthropic.messages.create(
        messages=[
            {
                "role": "user",
                "content": QUERY_PROMPT_TEMPLATE.format(
                    references=references, user_query=message.content
                ),
            }
        ],
        model="claude-sonnet-4-0",
        max_tokens=5000,
        system=system,
    )
    content = get_only_content(msg)
    chunks = iter(MarkdownChunker().split(content))
    await message.reply(next(chunks))
    for chunk in chunks:
        await message.channel.send(chunk)


async def on_message(message: Message) -> None:
    try:
        await generate_response(message)
    except anthropic_.RateLimitError:
        await message.reply("-# Rate limit for Anthropic exceeded.")
    except voyageai.error.RateLimitError:
        await message.reply("-# Rate limit for Voyage AI exceeded.")
    except anthropic_.InternalServerError:
        await message.reply("-# Anthropic servers overloaded.")
