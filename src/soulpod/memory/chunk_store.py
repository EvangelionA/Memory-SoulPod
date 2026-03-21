"""
Optional raw memory files (e.g. ``raw_memories.json``) beside the vector index.

Stub for extraction pipeline output; not used by the web app yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ChunkStoreStub:
    """Placeholder for loading and listing raw chunks from disk."""

    def __init__(self, memories_dir: Path) -> None:
        self._memories_dir = Path(memories_dir)

    def list_chunk_sources(self) -> list[Path]:
        """Return known chunk source paths if present (stub: empty)."""
        _ = self._memories_dir
        return []

    def load_raw(self) -> dict[str, Any]:
        """Placeholder for parsed raw memory payload."""
        return {}
