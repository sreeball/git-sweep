"""Snapshot support: save and load sweep results to/from JSON for auditing."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from git_sweep.reporter import SweepReport

DEFAULT_SNAPSHOT_DIR = Path.home() / ".git-sweep" / "snapshots"


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def snapshot_path(directory: Path = DEFAULT_SNAPSHOT_DIR, tag: str = "") -> Path:
    """Return a unique snapshot file path inside *directory*."""
    suffix = f"-{tag}" if tag else ""
    return directory / f"sweep-{_utcnow()}{suffix}.json"


def save_snapshot(
    report: SweepReport,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
    tag: str = "",
) -> Path:
    """Serialise *report* to a JSON snapshot file and return the path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = snapshot_path(directory, tag)
    payload: dict[str, Any] = {
        "created_at": _utcnow(),
        "dry_run": report.dry_run,
        "data": json.loads(report.format_json()),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(path: Path) -> dict[str, Any]:
    """Load a snapshot file and return the raw dict."""
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_snapshots(directory: Path = DEFAULT_SNAPSHOT_DIR) -> list[Path]:
    """Return snapshot files in *directory* sorted newest-first."""
    if not directory.exists():
        return []
    files = sorted(directory.glob("sweep-*.json"), reverse=True)
    return list(files)
