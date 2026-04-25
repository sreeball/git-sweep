"""Format and display branch age information for sweep reports."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from git_sweep.age_filter import AgeFilterResult
from git_sweep.output import print_info, print_warning


@dataclass
class BranchAgeEntry:
    repo_path: str
    branch: str
    last_commit: Optional[datetime]
    age_days: Optional[int]
    beyond_threshold: bool


def build_age_entries(
    repo_path: str, result: AgeFilterResult
) -> List[BranchAgeEntry]:
    """Convert an AgeFilterResult into a flat list of BranchAgeEntry records."""
    entries: List[BranchAgeEntry] = []
    now = datetime.now(tz=timezone.utc)

    for info in result.branches:
        age_days: Optional[int] = None
        if info.last_commit is not None:
            delta = now - info.last_commit.replace(tzinfo=timezone.utc)
            age_days = delta.days

        entries.append(
            BranchAgeEntry(
                repo_path=repo_path,
                branch=info.branch,
                last_commit=info.last_commit,
                age_days=age_days,
                beyond_threshold=info.branch in [
                    b.branch for b in result.stale
                ],
            )
        )
    return entries


def format_age_text(entries: List[BranchAgeEntry], threshold_days: int) -> str:
    """Return a human-readable summary of branch ages."""
    if not entries:
        return "No branch age data available."

    lines = [f"Branch age report (threshold: {threshold_days}d)"]
    lines.append("-" * 50)
    for e in entries:
        age_str = f"{e.age_days}d" if e.age_days is not None else "unknown"
        flag = "  [STALE]" if e.beyond_threshold else ""
        lines.append(f"  {e.repo_path}  {e.branch:<30} {age_str:>8}{flag}")
    return "\n".join(lines)


def format_age_json(entries: List[BranchAgeEntry]) -> str:
    """Return a JSON string of branch age entries."""
    data = [
        {
            "repo": e.repo_path,
            "branch": e.branch,
            "last_commit": e.last_commit.isoformat() if e.last_commit else None,
            "age_days": e.age_days,
            "stale": e.beyond_threshold,
        }
        for e in entries
    ]
    return json.dumps(data, indent=2)


def print_age_summary(
    entries: List[BranchAgeEntry], threshold_days: int
) -> None:
    """Print a concise age summary to stdout."""
    stale = [e for e in entries if e.beyond_threshold]
    print_info(f"Scanned {len(entries)} branch(es) across all repos.")
    if stale:
        print_warning(
            f"{len(stale)} branch(es) exceed the {threshold_days}-day threshold."
        )
    else:
        print_info("No stale branches found.")
