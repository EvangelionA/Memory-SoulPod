"""
Assemble the final system prompt from golden rules, package text, and optional runtime patch.

``src.server`` still uses ``config/app_runtime.json`` ``system_prompt`` only; this module is
for the next integration step (DigitalTwinPackage + runtime).
"""

from __future__ import annotations

from typing import Optional

from ..package_loader import LoadedSoulPackage
from .golden_rules import GOLDEN_RULES_SUMMARY


def build_system_prompt(
    *,
    package: Optional[LoadedSoulPackage] = None,
    runtime_system_prompt: str = "",
) -> str:
    """
    Build a single system string. If *package* is *None*, returns trimmed *runtime_system_prompt*
    and golden rules only when runtime is empty (stub behavior for tests).

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
    rt = (runtime_system_prompt or "").strip()
    if rt:
        parts.append(rt)
    return "\n\n".join(p for p in parts if p)
