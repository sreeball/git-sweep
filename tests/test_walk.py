"""Tests for git_sweep.walk."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from git_sweep.walk import collect_repos, find_repos


@pytest.fixture()
def fake_tree(tmp_path):
    """Create a small directory tree with two git repos."""
    repo_a = tmp_path / "projects" / "alpha"
    repo_b = tmp_path / "projects" / "beta"
    non_repo = tmp_path / "projects" / "docs"
    nested = tmp_path / "projects" / "alpha" / "sub"

    for d in (repo_a, repo_b, non_repo, nested):
        d.mkdir(parents=True)

    (repo_a / ".git").mkdir()
    (repo_b / ".git").mkdir()
    # nested .git should NOT be discovered because we stop at alpha
    (nested / ".git").mkdir()

    return tmp_path


def test_find_repos_discovers_git_dirs(fake_tree) -> None:
    repos = list(find_repos(str(fake_tree)))
    names = {os.path.basename(r) for r in repos}
    assert "alpha" in names
    assert "beta" in names


def test_find_repos_skips_non_repos(fake_tree) -> None:
    repos = list(find_repos(str(fake_tree)))
    names = {os.path.basename(r) for r in repos}
    assert "docs" not in names


def test_find_repos_does_not_recurse_into_repo(fake_tree) -> None:
    repos = list(find_repos(str(fake_tree)))
    # 'sub' is inside alpha which is already a repo; should not appear
    names = {os.path.basename(r) for r in repos}
    assert "sub" not in names


def test_find_repos_max_depth_zero(fake_tree) -> None:
    repos = list(find_repos(str(fake_tree), max_depth=0))
    assert repos == []


def test_collect_repos_deduplicates(fake_tree) -> None:
    root = str(fake_tree)
    repos = collect_repos([root, root])
    assert len(repos) == len(set(repos))


def test_collect_repos_skip_dirs(fake_tree) -> None:
    repos = collect_repos([str(fake_tree)], skip_dirs=["beta"])
    names = {os.path.basename(r) for r in repos}
    assert "beta" not in names
    assert "alpha" in names
