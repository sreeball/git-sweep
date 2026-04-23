"""Module for scanning git repositories and identifying merged/stale branches."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BranchInfo:
    name: str
    is_merged: bool
    last_commit_date: Optional[str] = None
    tracking_remote: Optional[str] = None


@dataclass
class RepoScanResult:
    path: Path
    merged_branches: list[BranchInfo] = field(default_factory=list)
    stale_branches: list[BranchInfo] = field(default_factory=list)
    error: Optional[str] = None


def _run_git(args: list[str], cwd: Path) -> tuple[str, str, int]:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def is_git_repo(path: Path) -> bool:
    """Check whether the given path is a git repository."""
    _, _, code = _run_git(["rev-parse", "--git-dir"], path)
    return code == 0


def get_merged_branches(path: Path, base_branch: str = "main") -> list[BranchInfo]:
    """Return local branches that have been merged into base_branch."""
    stdout, _, code = _run_git(
        ["branch", "--merged", base_branch, "--format=%(refname:short)"], path
    )
    if code != 0:
        return []

    branches = []
    for name in stdout.splitlines():
        name = name.strip()
        if not name or name == base_branch:
            continue
        date_out, _, _ = _run_git(
            ["log", "-1", "--format=%ci", name], path
        )
        branches.append(BranchInfo(name=name, is_merged=True, last_commit_date=date_out))
    return branches


def scan_repo(path: Path, base_branch: str = "main", stale_days: int = 90) -> RepoScanResult:
    """Scan a single repository for merged and stale branches."""
    result = RepoScanResult(path=path)

    if not is_git_repo(path):
        result.error = f"{path} is not a git repository"
        return result

    result.merged_branches = get_merged_branches(path, base_branch)

    stdout, _, code = _run_git(
        ["for-each-ref", "--sort=committerdate",
         f"--format=%(refname:short) %(committerdate:relative)",
         "refs/heads/"],
        path,
    )
    if code == 0:
        for line in stdout.splitlines():
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue
            name, rel_date = parts
            if name == base_branch:
                continue
            already_merged = any(b.name == name for b in result.merged_branches)
            if not already_merged and "months" in rel_date or "year" in rel_date:
                result.stale_branches.append(
                    BranchInfo(name=name, is_merged=False, last_commit_date=rel_date)
                )

    return result
