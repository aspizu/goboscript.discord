from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from redisvl.query import VectorQuery
from rich import print

from gbot.embedding import embed

from . import ant_client, google_client, index

MODEL_NAME = "claude-sonnet-4-0"
MAX_QUERY_RESULTS = 10
SYNTAX_GUIDE_PATH = Path("syntax_guide.txt")

prompts_path = Path("prompts")

_llm_failures: dict[str, float] = {}
LLM_FAILURE_TIMEOUT = 3600  # 1 hour in seconds


class LLMProvider(Protocol):
    async def __call__(self, prompt: str) -> str: ...


async def call_claude(prompt: str) -> str:
    message = await ant_client.messages.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )

    if not message.content:
        msg = "LLM returned no content"
        raise LLMResponseError(msg)

    text_content = next(
        (
            block.text  # pyright: ignore[]
            for block in message.content
            if getattr(block, "type", None) == "text"
        ),
        None,
    )

    if text_content is None:
        msg = "LLM returned unsupported content type"
        raise LLMResponseError(msg)

    return text_content


async def call_gemini(prompt: str) -> str:
    response = await google_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    if not response.text:
        msg = "Gemini returned no content"
        raise LLMResponseError(msg)

    return response.text


LLM_PROVIDERS = [
    ("claude", call_claude),
    ("gemini", call_gemini),
]


class RAGError(Exception): ...


class LLMResponseError(RAGError): ...


async def call_llm(prompt: str) -> str:
    global _llm_failures  # noqa: PLW0602
    current_time = time.time()
    available_providers = []
    for provider_name, provider_func in LLM_PROVIDERS:
        failure_time = _llm_failures.get(provider_name)
        if failure_time is not None:
            time_since_failure = current_time - failure_time
            if time_since_failure < LLM_FAILURE_TIMEOUT:
                continue
            _llm_failures.pop(provider_name, None)
        available_providers.append((provider_name, provider_func))
    for provider_name, provider_func in available_providers:
        try:
            return await provider_func(prompt)
        except Exception as exception:  # noqa: BLE001
            print(f"{provider_name} failed: {exception}")
            _llm_failures[provider_name] = current_time
    msg = "All LLM providers failed"
    raise LLMResponseError(msg)


async def get_vector_search_results(query_text: str) -> list[dict[str, str]]:
    embeddings = await embed([query_text])
    query = VectorQuery(
        vector=embeddings[0],
        vector_field_name="embedding",
        return_fields=["path", "text"],
        num_results=MAX_QUERY_RESULTS,
    )
    return await index.query(query)


def format_references(search_results: list[dict[str, str]]) -> str:
    return "\n".join(
        [f"{result['path']}:\n{result['text']}" for result in search_results]
    )


async def needs_syntax_guide(question: str) -> bool:
    prompt = prompts_path.joinpath("needs_syntax_guide.txt").read_text()
    response = await call_llm(prompt.format(question=question))
    return "true" in response.lower()


def load_syntax_guide() -> str:
    return SYNTAX_GUIDE_PATH.read_text(encoding="utf-8")


async def generate_response(question: str) -> str:
    search_results = await get_vector_search_results(question)
    references = format_references(search_results)

    if await needs_syntax_guide(question):
        syntax_guide = load_syntax_guide()
        if syntax_guide:
            references = syntax_guide + "\n" + references
    else:
        references += prompts_path.joinpath("no_syntax_guide_fix.txt").read_text()

    prompt = (
        prompts_path.joinpath("prompt.txt")
        .read_text()
        .format(question=question, references=references)
    )
    return await call_llm(prompt)
