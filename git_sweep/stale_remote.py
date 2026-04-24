"""Detect and remove stale remote-tracking branches (gone remotes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from git_sweep.repo_scanner import _run_git


@dataclass
class StaleRemoteInfo:
    """Represents a remote-tracking branch whose upstream is gone."""

    repo_path: str
    ref: str  # e.g. 'origin/feature-x'


@dataclass
class StaleRemoteResult:
    """Result of scanning a repo for stale remote-tracking branches."""

    repo_path: str
    stale: List[StaleRemoteInfo] = field(default_factory=list)
    error: str | None = None


def get_stale_remotes(repo_path: str) -> StaleRemoteResult:
    """Return remote-tracking branches marked as [gone] in *repo_path*.

    Runs ``git remote prune`` for each remote first so that the tracking
    information is up-to-date, then inspects ``git branch -vv`` output for
    entries annotated with ``[<remote>/<branch>: gone]``.
    """
    # Prune all remotes so refs reflect current server state.
    remotes_out, err = _run_git(["remote"], repo_path)
    if err:
        return StaleRemoteResult(repo_path=repo_path, error=err)

    for remote in remotes_out.splitlines():
        remote = remote.strip()
        if remote:
            _run_git(["remote", "prune", remote], repo_path)

    out, err = _run_git(["branch", "-vv"], repo_path)
    if err:
        return StaleRemoteResult(repo_path=repo_path, error=err)

    stale: List[StaleRemoteInfo] = []
    for line in out.splitlines():
        # Strip leading '*' marker for current branch.
        clean = line.lstrip("* ").strip()
        if not clean:
            continue
        # Format: <branch>  <sha>  [<remote>/<branch>: gone] <subject>
        if ": gone]" in clean:
            branch_name = clean.split()[0]
            stale.append(StaleRemoteInfo(repo_path=repo_path, ref=branch_name))

    return StaleRemoteResult(repo_path=repo_path, stale=stale)


def prune_stale_remotes(
    repo_path: str,
    dry_run: bool = True,
) -> StaleRemoteResult:
    """Delete local branches whose upstream tracking branch is gone.

    When *dry_run* is ``True`` the branches are discovered but not removed.
    """
    result = get_stale_remotes(repo_path)
    if dry_run or result.error or not result.stale:
        return result

    kept: List[StaleRemoteInfo] = []
    errors: List[str] = []
    for info in result.stale:
        _, err = _run_git(["branch", "-D", info.ref], repo_path)
        if err:
            errors.append(f"{info.ref}: {err}")
            kept.append(info)

    result.stale = [i for i in result.stale if i not in kept]
    if errors:
        result.error = "; ".join(errors)
    return result
