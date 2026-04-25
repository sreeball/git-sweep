"""Detect branches that may have been renamed (similar name, same tip commit)."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from git_sweep.repo_scanner import _run_git


@dataclass
class RenameCandidate:
    old_branch: str
    new_branch: str
    similarity: float  # 0.0 – 1.0
    tip_commit: str


@dataclass
class RenameDetectionResult:
    repo_path: str
    candidates: List[RenameCandidate] = field(default_factory=list)
    error: Optional[str] = None


def _branch_tips(repo_path: str) -> dict[str, str]:
    """Return {branch_name: tip_sha} for all local branches."""
    result = _run_git(
        ["git", "branch", "-v", "--no-abbrev", "--format=%(refname:short) %(objectname)"],
        cwd=repo_path,
    )
    tips: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            tips[parts[0]] = parts[1]
    return tips


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_rename_candidates(
    repo_path: str,
    merged_branches: List[str],
    threshold: float = 0.6,
) -> RenameDetectionResult:
    """For each merged branch check whether a surviving branch shares the same
    tip commit or a highly similar name, which suggests a rename rather than a
    true merge.
    """
    result = RenameDetectionResult(repo_path=repo_path)
    try:
        tips = _branch_tips(repo_path)
    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
        return result

    active_branches = set(tips.keys())
    merged_set = set(merged_branches)
    live_branches = active_branches - merged_set

    for merged in merged_set:
        merged_sha = tips.get(merged)
        for live in live_branches:
            live_sha = tips.get(live)
            same_tip = merged_sha and live_sha and merged_sha == live_sha
            sim = _similarity(merged, live)
            if same_tip or sim >= threshold:
                result.candidates.append(
                    RenameCandidate(
                        old_branch=merged,
                        new_branch=live,
                        similarity=round(sim, 3),
                        tip_commit=merged_sha or "",
                    )
                )
    return result
