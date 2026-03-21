# DigitalTwinPackage (user assets)

This folder holds **per-soul** packages. See `Core/description.md` and `Core/core.md` for the full spec.

- Do **not** commit real family data. Use a private path outside the repo for production pods.
- A valid package directory contains at least: `profile.json`, `system_prompts.txt`, `config.json`, and usually `memories/` and `assets/`.

Example layout (copy `_template` and rename):

```text
YourSoulName/
├── profile.json
├── system_prompts.txt
├── config.json
├── memories/
└── assets/
```

The Python loader lives in `src/soulpod/package_loader.py` and is **not** connected to the HTTP API yet.
