"""
Schema for per-package ``config.json`` (embedding, retrieval). See ``Core/core.md``.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class PackageConfig(BaseModel):
    """Technical knobs for one DigitalTwinPackage instance."""

    embedding_model: Optional[str] = Field(default=None, description="LiteLLM or local embedding id")
    retrieval_top_k: Optional[int] = Field(default=None, ge=1, le=100)
    extra: dict[str, Any] = Field(default_factory=dict)
