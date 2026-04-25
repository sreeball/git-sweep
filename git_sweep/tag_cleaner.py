"""Detect and optionally delete stale local tags not present on any remote."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from git_sweep.repo_scanner import _run_git


@dataclass
class StaleTagInfo:
    name: str
    sha: str


@dataclass
class TagCleanResult:
    repo_path: Path
    stale_tags: List[StaleTagInfo] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    error: Optional[str] = None


def get_stale_tags(repo_path: Path) -> TagCleanResult:
    """Return local tags that have no matching remote ref."""
    result = TagCleanResult(repo_path=repo_path)

    local = _run_git(["tag", "--list"], cwd=repo_path)
    if local.returncode != 0:
        result.error = local.stderr.strip()
        return result

    local_tags = [t.strip() for t in local.stdout.splitlines() if t.strip()]
    if not local_tags:
        return result

    remote = _run_git(["ls-remote", "--tags", "origin"], cwd=repo_path)
    if remote.returncode != 0:
        result.error = remote.stderr.strip()
        return result

    remote_tag_names: set[str] = set()
    for line in remote.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            ref = parts[1]  # refs/tags/v1.0 or refs/tags/v1.0^{}
            name = ref.replace("refs/tags/", "").rstrip("^{}")
            remote_tag_names.add(name)

    for tag in local_tags:
        if tag not in remote_tag_names:
            sha_proc = _run_git(["rev-list", "-n", "1", tag], cwd=repo_path)
            sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else ""
            result.stale_tags.append(StaleTagInfo(name=tag, sha=sha))

    return result


def delete_stale_tags(result: TagCleanResult, dry_run: bool = True) -> TagCleanResult:
    """Delete stale tags from the local repo (unless dry_run)."""
    for tag_info in result.stale_tags:
        if dry_run:
            result.deleted.append(tag_info.name)
            continue
        proc = _run_git(["tag", "-d", tag_info.name], cwd=result.repo_path)
        if proc.returncode == 0:
            result.deleted.append(tag_info.name)
        else:
            result.errors.append(f"{tag_info.name}: {proc.stderr.strip()}")
    return result
