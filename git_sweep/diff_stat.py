"""Compute per-branch diff statistics (commits ahead/behind, last author)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from git_sweep.repo_scanner import _run_git


@dataclass
class BranchDiffStat:
    branch: str
    commits_behind: int = 0
    commits_ahead: int = 0
    last_author: Optional[str] = None
    last_commit_date: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DiffStatResult:
    repo_path: str
    stats: List[BranchDiffStat] = field(default_factory=list)
    error: Optional[str] = None


def get_branch_diff_stat(
    repo_path: str,
    branch: str,
    base: str = "main",
) -> BranchDiffStat:
    """Return ahead/behind counts and last-commit metadata for *branch* vs *base*."""
    stat = BranchDiffStat(branch=branch)

    rev_result = _run_git(
        ["rev-list", "--left-right", "--count", f"{base}...{branch}"],
        cwd=repo_path,
    )
    if rev_result.returncode != 0:
        stat.error = rev_result.stderr.strip()
        return stat

    parts = rev_result.stdout.strip().split()
    if len(parts) == 2:
        stat.commits_behind = int(parts[0])
        stat.commits_ahead = int(parts[1])

    log_result = _run_git(
        ["log", "-1", "--format=%an|%ci", branch],
        cwd=repo_path,
    )
    if log_result.returncode == 0:
        raw = log_result.stdout.strip()
        if "|" in raw:
            author, date = raw.split("|", 1)
            stat.last_author = author.strip()
            stat.last_commit_date = date.strip()

    return stat


def collect_diff_stats(
    repo_path: str,
    branches: List[str],
    base: str = "main",
) -> DiffStatResult:
    """Collect diff stats for every branch in *branches*."""
    result = DiffStatResult(repo_path=repo_path)
    for branch in branches:
        result.stats.append(get_branch_diff_stat(repo_path, branch, base))
    return result
