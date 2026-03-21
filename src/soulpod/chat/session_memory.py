"""
Server-side session history (optional). Frontend currently sends full ``chatHistory``.

If you adopt RunnableWithMessageHistory (CloneLLM style), implement store here.
"""

from __future__ import annotations

from typing import Dict, List


class SessionMemoryStub:
    """In-process placeholder: session_id -> OpenAI-style message list."""

    def __init__(self) -> None:
        self._sessions: Dict[str, List[dict]] = {}

    def get(self, session_id: str) -> List[dict]:
        return list(self._sessions.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
