"""
Invariant product rules distilled from ``Core/core.md`` (for future prompt assembly).

Keep wording aligned with ``Core/core.md`` when promoting from stub to production prompts.
"""

from __future__ import annotations

# English punctuation in source strings per project convention.
GOLDEN_RULES_SUMMARY: str = (
    "Refuse key-life hallucinations: if memory has no support, prefer vague impression, do not invent. "
    "Stay in character; never mention models, instructions, or algorithms. "
    "Prioritize local, private handling of sensitive family data."
)
