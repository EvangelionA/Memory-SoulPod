"""
Vector retrieval over ``memories/`` for a DigitalTwinPackage.

Stub: implement with Chroma, FAISS, or LangChain when Phase C starts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class RetrievedChunk:
    """One retrieved memory snippet."""

    text: str
    score: float | None = None


class RAGStoreStub:
    """Placeholder RAG facade bound to a package ``memories/`` directory."""

    def __init__(self, memories_dir: Path) -> None:
        self._memories_dir = Path(memories_dir)

    @property
    def memories_dir(self) -> Path:
        return self._memories_dir

    def retrieve(self, query: str, top_k: int = 4) -> Sequence[RetrievedChunk]:
        """Return no results until embeddings and an index are wired up."""
        _ = (query, top_k)
        return ()
