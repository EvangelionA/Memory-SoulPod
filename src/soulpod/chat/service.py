"""
Single entry for ``messages -> reply`` (stream or full). Wire to ``src.liteLLM`` later.

``src.server`` keeps its own ``/chat`` and ``/chat/stream`` until this is adopted.
"""

from __future__ import annotations

from typing import Any, List


class ChatServiceStub:
    """Placeholder for unified chat pipeline (RAG + system prompt + LLM)."""

    async def complete(self, messages: List[dict[str, Any]]) -> str:
        """Non-streaming completion (not implemented)."""
        _ = messages
        raise NotImplementedError("ChatServiceStub.complete: integrate liteLLM or LangChain")

    async def stream(self, messages: List[dict[str, Any]]) -> None:
        """Streaming completion (not implemented; use ``ollama_chat_stream`` when wiring)."""
        _ = messages
        raise NotImplementedError("ChatServiceStub.stream: integrate liteLLM or LangChain")
