"""Tests for the repo_scanner module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_sweep.repo_scanner import (
    BranchInfo,
    RepoScanResult,
    get_merged_branches,
    is_git_repo,
    scan_repo,
)


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo for integration-style tests."""
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def test_is_git_repo_true(fake_repo: Path):
    assert is_git_repo(fake_repo) is True


def test_is_git_repo_false(tmp_path: Path):
    assert is_git_repo(tmp_path) is False


def test_get_merged_branches_empty(fake_repo: Path):
    branches = get_merged_branches(fake_repo, base_branch="main")
    assert branches == []


def test_get_merged_branches_detects_merged(fake_repo: Path):
    subprocess.run(["git", "checkout", "-b", "feature/x"], cwd=fake_repo, check=True, capture_output=True)
    (fake_repo / "x.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=fake_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add x"], cwd=fake_repo, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "main"], cwd=fake_repo, check=True, capture_output=True)
    subprocess.run(["git", "merge", "feature/x", "--no-ff"], cwd=fake_repo, check=True, capture_output=True)

    branches = get_merged_branches(fake_repo, base_branch="main")
    names = [b.name for b in branches]
    assert "feature/x" in names
    assert all(b.is_merged for b in branches)


def test_get_merged_branches_excludes_base_branch(fake_repo: Path):
    """The base branch itself should never appear in the merged branches list."""
    branches = get_merged_branches(fake_repo, base_branch="main")
    names = [b.name for b in branches]
    assert "main" not in names


def test_scan_repo_non_repo(tmp_path: Path):
    result = scan_repo(tmp_path)
    assert result.error is not None
    assert "not a git repository" in result.error


def test_scan_repo_returns_result_type(fake_repo: Path):
    result = scan_repo(fake_repo)
    assert isinstance(result, RepoScanResult)
    assert result.error is None
    assert result.path == fake_repo
