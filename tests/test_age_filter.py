"""Tests for git_sweep.age_filter."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from git_sweep.age_filter import (
    filter_by_age,
    get_branch_age,
    parse_age_threshold,
)
from git_sweep.repo_scanner import BranchInfo


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _fake_run(stdout: str, returncode: int = 0):
    def _run(cmd, cwd=None, **kw):
        return SimpleNamespace(stdout=stdout, returncode=returncode)
    return _run


# --- parse_age_threshold ---

def test_parse_days():
    assert parse_age_threshold("30d") == 30


def test_parse_weeks():
    assert parse_age_threshold("2w") == 14


def test_parse_months():
    assert parse_age_threshold("3m") == 90


def test_parse_invalid_raises():
    with pytest.raises(ValueError, match="Invalid age spec"):
        parse_age_threshold("5y")


# --- get_branch_age ---

def test_get_branch_age_ok():
    ts = int(NOW.timestamp())
    with patch("git_sweep.age_filter._run_git", _fake_run(str(ts))):
        result = get_branch_age("/repo", "main")
    assert result == NOW


def test_get_branch_age_error_returns_none():
    with patch("git_sweep.age_filter._run_git", _fake_run("", returncode=1)):
        result = get_branch_age("/repo", "main")
    assert result is None


# --- filter_by_age ---

def _make_branches(*names):
    return [BranchInfo(name=n, is_merged=True) for n in names]


def test_filter_stale_branch():
    old_ts = int((NOW - timedelta(days=60)).timestamp())
    with patch("git_sweep.age_filter.get_branch_age", return_value=NOW - timedelta(days=60)):
        result = filter_by_age("/repo", _make_branches("old-feature"), max_age_days=30, now=NOW)
    assert len(result.stale_branches) == 1
    assert result.stale_branches[0].name == "old-feature"
    assert result.skipped == []


def test_filter_fresh_branch_skipped():
    with patch("git_sweep.age_filter.get_branch_age", return_value=NOW - timedelta(days=5)):
        result = filter_by_age("/repo", _make_branches("fresh"), max_age_days=30, now=NOW)
    assert result.stale_branches == []
    assert len(result.skipped) == 1


def test_filter_unknown_age_skipped():
    with patch("git_sweep.age_filter.get_branch_age", return_value=None):
        result = filter_by_age("/repo", _make_branches("mystery"), max_age_days=30, now=NOW)
    assert result.stale_branches == []
    assert result.skipped[0].name == "mystery"
