"""Configuration loading and validation for git-sweep."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


DEFAULT_CONFIG_FILENAME = ".git-sweep.toml"
DEFAULT_PROTECTED_BRANCHES = ["main", "master", "develop", "staging", "production"]


@dataclass
class SweepConfig:
    """Holds runtime configuration for a git-sweep run."""

    repos: List[str] = field(default_factory=list)
    protected_branches: List[str] = field(
        default_factory=lambda: list(DEFAULT_PROTECTED_BRANCHES)
    )
    delete_remote: bool = False
    dry_run: bool = True
    remote_name: str = "origin"
    older_than_days: Optional[int] = None

    def is_protected(self, branch: str) -> bool:
        """Return True if *branch* should never be deleted."""
        return branch in self.protected_branches


def _find_config_file(start: Path) -> Optional[Path]:
    """Walk up from *start* looking for a config file."""
    current = start.resolve()
    for directory in [current, *current.parents]:
        candidate = directory / DEFAULT_CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return None


def load_config(config_path: Optional[str] = None) -> SweepConfig:
    """Load a :class:`SweepConfig` from *config_path* or auto-discovered file.

    Falls back to defaults when no file is found or TOML support is unavailable.
    """
    path: Optional[Path] = None

    if config_path:
        path = Path(config_path)
    else:
        path = _find_config_file(Path(os.getcwd()))

    if path is None or tomllib is None:
        return SweepConfig()

    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    sweep_section = data.get("sweep", {})

    protected = sweep_section.get(
        "protected_branches", list(DEFAULT_PROTECTED_BRANCHES)
    )

    return SweepConfig(
        repos=sweep_section.get("repos", []),
        protected_branches=protected,
        delete_remote=sweep_section.get("delete_remote", False),
        dry_run=sweep_section.get("dry_run", True),
        remote_name=sweep_section.get("remote", "origin"),
        older_than_days=sweep_section.get("older_than_days", None),
    )
