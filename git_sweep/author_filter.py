"""Filter branches by author name or email."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from git_sweep.repo_scanner import BranchInfo, RepoScanResult, _run_git


@dataclass
class AuthorFilterResult:
    repo_path: str
    matched: List[BranchInfo] = field(default_factory=list)
    skipped: List[BranchInfo] = field(default_factory=list)
    error: Optional[str] = None


def get_branch_author(repo_path: str, branch: str) -> Optional[str]:
    """Return 'Name <email>' for the latest commit on *branch*, or None."""
    result = _run_git(
        ["log", "-1", "--format=%an <%ae>", branch],
        cwd=repo_path,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _matches(author_string: Optional[str], pattern: str) -> bool:
    """Case-insensitive substring match against name or email."""
    if author_string is None:
        return False
    return pattern.lower() in author_string.lower()


def filter_by_author(
    scan_result: RepoScanResult,
    pattern: str,
) -> AuthorFilterResult:
    """Split *scan_result* branches into matched / skipped by *pattern*."""
    out = AuthorFilterResult(repo_path=scan_result.repo_path)
    if scan_result.error:
        out.error = scan_result.error
        return out

    for branch in scan_result.merged_branches:
        author = get_branch_author(scan_result.repo_path, branch.name)
        if _matches(author, pattern):
            out.matched.append(branch)
        else:
            out.skipped.append(branch)
    return out
