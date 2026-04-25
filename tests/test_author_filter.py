"""Tests for git_sweep.author_filter."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from git_sweep.repo_scanner import BranchInfo, RepoScanResult
from git_sweep.author_filter import (
    AuthorFilterResult,
    _matches,
    filter_by_author,
    get_branch_author,
)


def _proc(stdout: str, returncode: int = 0) -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, returncode=returncode)


# ---------------------------------------------------------------------------
# _matches
# ---------------------------------------------------------------------------

def test_matches_by_name():
    assert _matches("Alice Smith <alice@example.com>", "alice") is True


def test_matches_by_email():
    assert _matches("Bob <bob@corp.io>", "corp.io") is True


def test_matches_case_insensitive():
    assert _matches("Carol <carol@x.com>", "CAROL") is True


def test_no_match():
    assert _matches("Dave <dave@y.com>", "alice") is False


def test_matches_none_author():
    assert _matches(None, "alice") is False


# ---------------------------------------------------------------------------
# get_branch_author
# ---------------------------------------------------------------------------

def test_get_branch_author_returns_string():
    with patch("git_sweep.author_filter._run_git", return_value=_proc("Alice <a@b.com>")):
        result = get_branch_author("/repo", "feature/x")
    assert result == "Alice <a@b.com>"


def test_get_branch_author_git_error_returns_none():
    with patch("git_sweep.author_filter._run_git", return_value=_proc("", returncode=128)):
        result = get_branch_author("/repo", "bad-branch")
    assert result is None


def test_get_branch_author_empty_output_returns_none():
    with patch("git_sweep.author_filter._run_git", return_value=_proc("")):
        result = get_branch_author("/repo", "branch")
    assert result is None


# ---------------------------------------------------------------------------
# filter_by_author
# ---------------------------------------------------------------------------

def _scan(branches, error=None):
    return RepoScanResult(
        repo_path="/repo",
        merged_branches=[BranchInfo(name=b) for b in branches],
        error=error,
    )


def test_filter_by_author_matches_branch():
    scan = _scan(["feature/a", "feature/b"])
    authors = {"feature/a": "Alice <a@x.com>", "feature/b": "Bob <b@x.com>"}
    with patch("git_sweep.author_filter.get_branch_author", side_effect=lambda r, b: authors[b]):
        result = filter_by_author(scan, "alice")
    assert len(result.matched) == 1
    assert result.matched[0].name == "feature/a"
    assert len(result.skipped) == 1


def test_filter_by_author_no_match():
    scan = _scan(["feature/a"])
    with patch("git_sweep.author_filter.get_branch_author", return_value="Bob <b@x.com>"):
        result = filter_by_author(scan, "carol")
    assert result.matched == []
    assert len(result.skipped) == 1


def test_filter_by_author_propagates_scan_error():
    scan = _scan([], error="git failed")
    result = filter_by_author(scan, "alice")
    assert result.error == "git failed"
    assert result.matched == []
