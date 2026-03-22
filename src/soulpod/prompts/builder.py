"""
Assemble the final system prompt from golden rules, package text, and optional runtime patch.

When a package is active, ``src.server`` uses ``build_system_prompt``; otherwise only
``system_prompt`` from runtime config is applied (no golden rules in that path).
"""

from __future__ import annotations

from typing import Optional

from ..package_loader import LoadedSoulPackage
from .golden_rules import GOLDEN_RULES_SUMMARY


def _profile_compact_block(package: LoadedSoulPackage) -> str:
    """Short structured summary for the model (keeps tokens bounded)."""
    p = package.profile
    lines = [f"Display name: {p.display_name}"]
    if p.relationship_to_user:
        lines.append(f"Relationship to user: {p.relationship_to_user}")
    if p.notes:
        lines.append(f"Notes: {p.notes}")
    return "Known about this person (structured):\n" + "\n".join(lines)


def build_system_prompt(
    *,
    package: Optional[LoadedSoulPackage] = None,
    runtime_system_prompt: str = "",
) -> str:
    """
    Build a single system string when a DigitalTwinPackage is active: golden rules,
    ``system_prompts.txt``, compact profile block, then optional runtime patch.

    When *package* is *None*, this function is not used for HTTP (server keeps legacy:
    runtime ``system_prompt`` only). Callers may pass *package* only for tests.

    Args:
        package: Loaded DigitalTwinPackage, or *None*.
        runtime_system_prompt: Optional extra instructions (e.g. from app_runtime.json).

    Returns:
        Combined system prompt text.
    """
    parts: list[str] = []
    parts.append(GOLDEN_RULES_SUMMARY.strip())
    if package is not None:
        parts.append(package.system_prompts_text.strip())
        parts.append(_profile_compact_block(package))
    rt = (runtime_system_prompt or "").strip()
    if rt:
        parts.append(rt)
    return "\n\n".join(p for p in parts if p)
