"""
Load and validate a DigitalTwinPackage directory (profile, prompts, config, memories).

Not wired into ``src.server`` yet; safe to evolve without affecting current APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .schemas.package_config import PackageConfig
from .schemas.profile import SoulProfile


@dataclass(frozen=True)
class LoadedSoulPackage:
    """In-memory view of a package after load (minimal fields for now)."""

    root: Path
    profile: SoulProfile
    tech_config: PackageConfig
    system_prompts_text: str


def load_soul_package(root: Path | str) -> LoadedSoulPackage:
    """
    Load *root* as a DigitalTwinPackage: ``profile.json``, ``config.json``,
    ``system_prompts.txt``. Optional dirs ``memories/``, ``assets/`` are not read here yet.

    Raises:
        FileNotFoundError: If required files are missing.
        ValidationError: If JSON does not match schemas.
    """
    path = Path(root).expanduser().resolve()
    profile_path = path / "profile.json"
    config_path = path / "config.json"
    prompts_path = path / "system_prompts.txt"

    if not profile_path.is_file():
        raise FileNotFoundError(f"Missing profile.json: {profile_path}")
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing config.json: {config_path}")
    if not prompts_path.is_file():
        raise FileNotFoundError(f"Missing system_prompts.txt: {prompts_path}")

    profile = SoulProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))
    tech_config = PackageConfig.model_validate_json(config_path.read_text(encoding="utf-8"))
    system_prompts_text = prompts_path.read_text(encoding="utf-8")

    return LoadedSoulPackage(
        root=path,
        profile=profile,
        tech_config=tech_config,
        system_prompts_text=system_prompts_text,
    )


def try_load_soul_package(root: Path | str) -> Optional[LoadedSoulPackage]:
    """Return a loaded package, or *None* if paths or validation fail."""
    try:
        return load_soul_package(root)
    except (OSError, ValidationError, FileNotFoundError, ValueError):
        return None
