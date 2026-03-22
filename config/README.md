# Runtime configuration

- **`app_runtime.json`** — Local runtime settings (model, `api_base`, `system_prompt`, `api_key`, optional `soul_package_enabled`, `soul_package_path`). **Gitignored**; do not commit real API keys.
- **`app_runtime.example.json`** — Template with empty `api_key` and placeholders; safe to commit. Copy to `app_runtime.json` and edit, or use **Settings** in the web UI (`/settings`).

The server reads `app_runtime.json` on each request; restart is not required after edits from the UI.

Optional: `.env.example` at repo root documents future env-based tooling; the app does not load `.env` by default.
