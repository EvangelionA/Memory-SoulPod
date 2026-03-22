"""
Schema for ``profile.json`` (DigitalTwinPackage). Extend per ``Core/description.md``.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SoulProfile(BaseModel):
    """
    Minimal profile placeholder. Add Big Five, relations, and style fields in later phases.
    """

    schema_version: int = Field(default=1, ge=1, description="Package JSON schema revision")
    display_name: str = Field(..., description="Name or how the user addresses this soul")
    relationship_to_user: Optional[str] = Field(
        default=None, description="e.g. father, grandmother (localized string)"
    )
    notes: Optional[str] = Field(default=None, description="Freeform until schema stabilizes")
    extra: dict[str, Any] = Field(default_factory=dict, description="Forward-compatible bag")
