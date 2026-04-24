"""Branch cleaning logic for git-sweep.

Provides functions to delete merged local and remote branches,
with dry-run support and configurable protection lists.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from git_sweep.repo_scanner import BranchInfo, _run_git


# Branches that should never be deleted, regardless of merge status
DEFAULT_PROTECTED_BRANCHES = frozenset({
    "main",
    "master",
    "develop",
    "dev",
    "staging",
    "production",
    "release",
})


@dataclass
class CleanResult:
    """Result of a branch cleanup operation on a single repository."""

    repo_path: str
    deleted_local: List[str] = field(default_factory=list)
    deleted_remote: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def total_deleted(self) -> int:
        return len(self.deleted_local) + len(self.deleted_remote)

    def summary(self) -> str:
        prefix = "[DRY RUN] " if self.dry_run else ""
        lines = [f"{prefix}Repository: {self.repo_path}"]
        if self.deleted_local:
            lines.append(f"  Local branches deleted ({len(self.deleted_local)}):")
            for b in self.deleted_local:
                lines.append(f"    - {b}")
        if self.deleted_remote:
            lines.append(f"  Remote branches deleted ({len(self.deleted_remote)}):")
            for b in self.deleted_remote:
                lines.append(f"    - {b}")
        if self.skipped:
            lines.append(f"  Skipped (protected) ({len(self.skipped)}):")
            for b in self.skipped:
                lines.append(f"    ~ {b}")
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    ! {e}")
        if not self.deleted_local and not self.deleted_remote:
            lines.append("  Nothing to clean up.")
        return "\n".join(lines)


def delete_local_branch(
    repo_path: str,
    branch: str,
    force: bool = False,
) -> Optional[str]:
    """Delete a local branch. Returns an error message on failure, or None on success."""
    flag = "-D" if force else "-d"
    try:
        _run_git(["branch", flag, branch], cwd=repo_path)
        return None
    except subprocess.CalledProcessError as exc:
        return exc.stderr.strip() if exc.stderr else str(exc)


def delete_remote_branch(
    repo_path: str,
    remote: str,
    branch: str,
) -> Optional[str]:
    """Delete a remote tracking branch. Returns an error message on failure, or None on success."""
    try:
        _run_git(["push", remote, "--delete", branch], cwd=repo_path)
        return None
    except subprocess.CalledProcessError as exc:
        return exc.stderr.strip() if exc.stderr else str(exc)


def clean_merged_branches(
    repo_path: str,
    branches: List[BranchInfo],
    dry_run: bool = True,
    delete_remote: bool = False,
    force: bool = False,
    protected: Optional[frozenset] = None,
) -> CleanResult:
    """Delete merged branches from a repository.

    Args:
        repo_path: Absolute path to the git repository.
        branches: List of BranchInfo objects to consider for deletion.
        dry_run: If True, report what would be deleted without making changes.
        delete_remote: If True, also delete the corresponding remote branch.
        force: If True, use force-delete for local branches (git branch -D).
        protected: Set of branch names to never delete. Defaults to DEFAULT_PROTECTED_BRANCHES.

    Returns:
        A CleanResult summarising what was (or would be) deleted.
    """
    if protected is None:
        protected = DEFAULT_PROTECTED_BRANCHES

    result = CleanResult(repo_path=repo_path, dry_run=dry_run)

    for branch_info in branches:
        name = branch_info.name

        if name in protected:
            result.skipped.append(name)
            continue

        if not dry_run:
            err = delete_local_branch(repo_path, name, force=force)
            if err:
                result.errors.append(f"{name}: {err}")
                continue

        result.deleted_local.append(name)

        # Optionally remove the upstream remote branch
        if delete_remote and branch_info.upstream_remote and branch_info.upstream_branch:
            if not dry_run:
                err = delete_remote_branch(
                    repo_path,
                    branch_info.upstream_remote,
                    branch_info.upstream_branch,
                )
                if err:
                    result.errors.append(
                        f"{branch_info.upstream_remote}/{branch_info.upstream_branch}: {err}"
                    )
                    continue
            result.deleted_remote.append(
                f"{branch_info.upstream_remote}/{branch_info.upstream_branch}"
            )

    return result
