"""Filter branches by age based on last commit date."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from git_sweep.repo_scanner import BranchInfo, _run_git


@dataclass
class AgeFilterResult:
    repo_path: str
    stale_branches: List[BranchInfo]
    skipped: List[BranchInfo]
    error: Optional[str] = None


def get_branch_age(repo_path: str, branch: str) -> Optional[datetime]:
    """Return the UTC datetime of the last commit on *branch*, or None on error."""
    result = _run_git(
        ["log", "-1", "--format=%ct", branch],
        cwd=repo_path,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        ts = int(result.stdout.strip())
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except ValueError:
        return None


def parse_age_threshold(spec: str) -> int:
    """Parse an age string like '30d', '2w', '6m' into a number of days."""
    match = re.fullmatch(r"(\d+)([dwm])", spec.strip().lower())
    if not match:
        raise ValueError(f"Invalid age spec {spec!r}. Use e.g. '30d', '2w', '6m'.")
    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"d": 1, "w": 7, "m": 30}
    return value * multipliers[unit]


def filter_by_age(
    repo_path: str,
    branches: List[BranchInfo],
    max_age_days: int,
    now: Optional[datetime] = None,
) -> AgeFilterResult:
    """Split *branches* into stale (older than *max_age_days*) and skipped."""
    if now is None:
        now = datetime.now(tz=timezone.utc)

    stale: List[BranchInfo] = []
    skipped: List[BranchInfo] = []

    for branch in branches:
        age = get_branch_age(repo_path, branch.name)
        if age is None:
            skipped.append(branch)
            continue
        delta = (now - age).days
        if delta >= max_age_days:
            stale.append(branch)
        else:
            skipped.append(branch)

    return AgeFilterResult(repo_path=repo_path, stale_branches=stale, skipped=skipped)
