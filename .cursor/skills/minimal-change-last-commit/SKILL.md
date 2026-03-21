---
name: minimal-change-last-commit
description: >-
  Constrains edits to the smallest diff against the latest git commit, without
  changing behavior or broadening scope. Use when the user asks for minimal
  changes, incremental fixes, refactor-without-behavior-change, or to avoid
  over-editing compared to the last commit.
---

# Minimal change vs last commit

## Scope

- **Baseline**: `git diff HEAD` (or staged vs `HEAD` if committing). Treat **only** what the user asked for plus what is strictly required to implement it.
- **Do not** restyle unrelated files, rename symbols project-wide, or "clean up" modules that are outside the diff unless the user explicitly expands scope.

## Rules

1. **Smallest diff**: Prefer deleting lines over rewriting blocks; prefer local edits over new abstractions; avoid new dependencies unless necessary.
2. **Behavior unchanged**: After edits, the same inputs and user flows must behave as before, unless the user requested a behavior change. If you must change a public API, keep backward compatibility when feasible.
3. **Compare to last commit only**: Use the previous commit as the reference for "what changed." Do not assume older history or hypothetical ideal code unless the user points to it.
4. **Docs and noise**: Update docs only when the user-facing contract or routes change. Do not expand README or comments beyond what the delta requires.
5. **Review before finish**: Re-read the diff; if a hunk is not required for the request, revert it.

## Quick check

```bash
git diff HEAD
```

If the diff touches files or concerns not mentioned in the task, trim it.
