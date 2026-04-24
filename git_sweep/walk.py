"""Walk a root directory tree to find all git repositories."""

from __future__ import annotations

import os
from typing import Iterator, List, Optional

from git_sweep.repo_scanner import is_git_repo


def find_repos(
    root: str,
    max_depth: int = 3,
    skip_dirs: Optional[List[str]] = None,
) -> Iterator[str]:
    """Yield absolute paths of git repositories found under *root*.

    Stops descending once *max_depth* is reached or a .git directory is found
    (nested repos are not traversed further).
    """
    skip = set(skip_dirs or [])
    root = os.path.abspath(root)

    def _walk(path: str, depth: int) -> Iterator[str]:
        if depth > max_depth:
            return
        if is_git_repo(path):
            yield path
            return  # do not recurse into sub-repos
        try:
            entries = os.scandir(path)
        except PermissionError:
            return
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            if entry.name.startswith(".") or entry.name in skip:
                continue
            yield from _walk(entry.path, depth + 1)

    yield from _walk(root, 0)


def collect_repos(
    paths: List[str],
    max_depth: int = 3,
    skip_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Return a deduplicated, sorted list of repo paths from one or more roots."""
    seen: set[str] = set()
    result: List[str] = []
    for p in paths:
        for repo in find_repos(p, max_depth=max_depth, skip_dirs=skip_dirs):
            if repo not in seen:
                seen.add(repo)
                result.append(repo)
    return sorted(result)
