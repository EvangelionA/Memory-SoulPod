"""LiteLLM 封装的 Ollama 调用，支持流式与非流式。"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional

from litellm import acompletion

DEFAULT_MODEL = "ollama/qwen3:8b"
DEFAULT_API_BASE = "http://localhost:11434"


def _extract_message_content(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except Exception:
        content = ""
    return (content or "").strip()


async def ollama_chat_stream(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    api_base: str = DEFAULT_API_BASE,
    extra_params: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    """
    Call Ollama via LiteLLM and yield streaming delta chunks.

    Args:
        messages: OpenAI-style chat messages, e.g. [{"role":"user","content":"hi"}].
        model: LiteLLM model id, e.g. "ollama/llama3" or "ollama/qwen3:8b".
        api_base: Ollama server base URL, default "http://localhost:11434".
        extra_params: Optional extra kwargs passed to acompletion.

    Yields:
        Text deltas as they arrive.
    """
    params: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "api_base": api_base,
    }
    if extra_params:
        params.update(extra_params)

    response = await acompletion(**params)
    async for chunk in response:
        try:
            delta = chunk.choices[0].delta.content
        except Exception:
            delta = None
        if delta:
            yield delta


async def ollama_chat(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    api_base: str = DEFAULT_API_BASE,
    stream: bool = False,
    extra_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Call Ollama via LiteLLM and return a full text reply.

    Args:
        messages: OpenAI-style chat messages, e.g. [{"role":"user","content":"hi"}].
        model: LiteLLM model id, e.g. "ollama/llama3" or "ollama/qwen3:8b".
        api_base: Ollama server base URL, default "http://localhost:11434".
        stream: If True, use streaming and aggregate delta chunks.
        extra_params: Optional extra kwargs passed to acompletion.

    Returns:
        Assistant reply as plain text.
    """
    if stream:
        full_response = ""
        async for delta in ollama_chat_stream(
            messages=messages,
            model=model,
            api_base=api_base,
            extra_params=extra_params,
        ):
            full_response += delta
        return full_response

    params: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "api_base": api_base,
    }
    if extra_params:
        params.update(extra_params)

    response = await acompletion(**params)
    return _extract_message_content(response)


if __name__ == "__main__":
    import asyncio
    import sys

    async def _demo() -> None:
        async for delta in ollama_chat_stream(
            messages=[{"role": "user", "content": "你是谁"}],
            model="ollama/qwen3:8b",
        ):
            sys.stdout.write(delta)
            sys.stdout.flush()
        sys.stdout.write("\n")

    asyncio.run(_demo())
