# Repository layout (SoulPod engine vs assets)

## Runtime (unchanged for users)

- `python -m src.core` starts FastAPI in `src/server.py`.
- Web UI: `index.html`, `settings.html`; API: `/chat`, `/chat/stream`, `/api/runtime-config`, `/status`.

## New engine package (not wired to HTTP yet)

- `src/soulpod/` — DigitalTwinPackage load, prompt builder, RAG and chat stubs.
- `packages/` — user soul packages; see `packages/README.md`.
- `tools/extraction/`, `tools/persona_infer/` — offline pipelines.

## Canonical product docs

- `Core/core.md`, `Core/description.md` — vision, trinity architecture, golden rules.

Integration plan: call `build_system_prompt` and `load_soul_package` from `src/server.py` only after adding a safe config switch and UI for package path, without breaking existing `system_prompt` behavior.

**Detailed phased implementation (CloneLLM reference, Core alignment, acceptance criteria):** see [`docs/implementation_pipeline.md`](implementation_pipeline.md).
