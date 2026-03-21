"""Pydantic schemas for ``profile.json`` and ``config.json``."""

from .package_config import PackageConfig
from .profile import SoulProfile

__all__ = ("PackageConfig", "SoulProfile")
