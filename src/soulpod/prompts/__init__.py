"""Prompt assembly: golden rules plus per-package ``system_prompts.txt``."""

from .builder import build_system_prompt
from .golden_rules import GOLDEN_RULES_SUMMARY

__all__ = ("GOLDEN_RULES_SUMMARY", "build_system_prompt")
