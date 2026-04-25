"""Scan a single git repository for merged and stale branches."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BranchInfo:
    name: str
    is_merged: bool = False
    last_author: Optional[str] = None
    last_commit_date: Optional[str] = None


@dataclass
class RepoScanResult:
    repo_path: str
    merged_branches: List[BranchInfo] = field(default_factory=list)
    error: Optional[str] = None


def _run_git(cmd: List[str], cwd: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        **kwargs,
    )


def is_git_repo(path: str) -> bool:
    """Return True if *path* is the root of a git repository."""
    result = _run_git(["rev-parse", "--git-dir"], cwd=path)
    return result.returncode == 0


def get_merged_branches(
    repo_path: str,
    base_branch: str = "main",
    protected: Optional[List[str]] = None,
) -> RepoScanResult:
    """Return branches fully merged into *base_branch*."""
    if protected is None:
        protected = ["main", "master", "develop", "HEAD"]

    result = _run_git(
        ["branch", "--merged", base_branch],
        cwd=repo_path,
    )
    if result.returncode != 0:
        return RepoScanResult(
            repo_path=repo_path,
            error=result.stderr.strip() or "git branch --merged failed",
        )

    branches: List[BranchInfo] = []
    for line in result.stdout.splitlines():
        name = line.strip().lstrip("* ").strip()
        if not name or name in protected:
            continue
        branches.append(BranchInfo(name=name, is_merged=True))

    return RepoScanResult(repo_path=repo_path, merged_branches=branches)


def enrich_branch_info(repo_path: str, branch: BranchInfo) -> BranchInfo:
    """Populate last_author and last_commit_date on *branch* in-place."""
    result = _run_git(
        ["log", "-1", "--format=%an|%ci", branch.name],
        cwd=repo_path,
    )
    if result.returncode == 0 and "|" in result.stdout:
        author, date = result.stdout.strip().split("|", 1)
        branch.last_author = author.strip()
        branch.last_commit_date = date.strip()
    return branch
