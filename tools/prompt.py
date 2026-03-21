"""
Central registry of tool-related prompts for LLM calls (function-calling, JSON output,
connection checks, etc.).

Add new entries to TOOL_PROMPTS or define named string constants below, then import where needed,
e.g. from tools.prompt import TOOL_PROMPTS, get_tool_prompt.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Named prompts (prefer these for stable imports and refactors)
# ---------------------------------------------------------------------------

# Example: system fragment instructing the model how to emit tool calls.
TOOL_CALLING_SYSTEM_HINT: Final[str] = (
    "When a tool is required, respond with a single JSON object matching the requested schema. "
    "Do not wrap it in markdown code fences unless asked."
)

# Minimal user message to verify the LLM endpoint responds (parse reply for TRUE/FALSE).
LLM_CONNECTION_VERIFY_PROMPT: Final[str] = (
    "不需要思考，请立即回答，如果你能成功回复，请回复TRUE，否则回复FALSE"
)

# ---------------------------------------------------------------------------
# Registry (optional): key -> prompt text for dynamic lookup
# ---------------------------------------------------------------------------

TOOL_PROMPTS: Final[dict[str, str]] = {
    "tool_calling_system_hint": TOOL_CALLING_SYSTEM_HINT,
    "llm_connection_verify": LLM_CONNECTION_VERIFY_PROMPT,
}


def get_tool_prompt(name: str, default: str = "") -> str:
    """
    Return a registered tool prompt by key, or *default* if missing.

    Args:
        name: Key in TOOL_PROMPTS.
        default: Value when *name* is not found.

    Returns:
        Prompt string.
    """
    return TOOL_PROMPTS.get(name, default)
