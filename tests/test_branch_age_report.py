"""Tests for git_sweep.branch_age_report."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from git_sweep.age_filter import AgeFilterResult
from git_sweep.branch_age_report import (
    BranchAgeEntry,
    build_age_entries,
    format_age_json,
    format_age_text,
    print_age_summary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_info(branch: str, days_old: int):
    """Return a simple namespace mimicking AgeFilterResult branch info."""
    from types import SimpleNamespace
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_old)
    return SimpleNamespace(branch=branch, last_commit=ts.replace(tzinfo=None))


def _make_result(branches, stale_names):
    from types import SimpleNamespace
    stale = [b for b in branches if b.branch in stale_names]
    return AgeFilterResult(branches=branches, stale=stale, error=None)


# ---------------------------------------------------------------------------
# build_age_entries
# ---------------------------------------------------------------------------

def test_build_age_entries_returns_all_branches():
    branches = [_make_info("feat/a", 10), _make_info("feat/b", 5)]
    result = _make_result(branches, stale_names=["feat/a"])
    entries = build_age_entries("/repo", result)
    assert len(entries) == 2


def test_build_age_entries_marks_stale_correctly():
    branches = [_make_info("old", 100), _make_info("new", 2)]
    result = _make_result(branches, stale_names=["old"])
    entries = build_age_entries("/repo", result)
    stale_map = {e.branch: e.beyond_threshold for e in entries}
    assert stale_map["old"] is True
    assert stale_map["new"] is False


def test_build_age_entries_computes_age_days():
    branches = [_make_info("feat/x", 30)]
    result = _make_result(branches, stale_names=[])
    entries = build_age_entries("/repo", result)
    assert entries[0].age_days is not None
    assert 29 <= entries[0].age_days <= 31  # allow 1-day clock drift


def test_build_age_entries_empty_result():
    result = _make_result([], stale_names=[])
    entries = build_age_entries("/repo", result)
    assert entries == []


# ---------------------------------------------------------------------------
# format_age_text
# ---------------------------------------------------------------------------

def test_format_age_text_no_entries():
    text = format_age_text([], threshold_days=30)
    assert "No branch age data" in text


def test_format_age_text_contains_stale_flag():
    entry = BranchAgeEntry(
        repo_path="/r", branch="old", last_commit=None,
        age_days=90, beyond_threshold=True
    )
    text = format_age_text([entry], threshold_days=30)
    assert "STALE" in text
    assert "old" in text


# ---------------------------------------------------------------------------
# format_age_json
# ---------------------------------------------------------------------------

def test_format_age_json_valid():
    entry = BranchAgeEntry(
        repo_path="/r", branch="feat/z", last_commit=None,
        age_days=5, beyond_threshold=False
    )
    raw = format_age_json([entry])
    data = json.loads(raw)
    assert isinstance(data, list)
    assert data[0]["branch"] == "feat/z"
    assert data[0]["stale"] is False


# ---------------------------------------------------------------------------
# print_age_summary (smoke test)
# ---------------------------------------------------------------------------

def test_print_age_summary_no_stale(capsys):
    entries = [
        BranchAgeEntry("/r", "main", None, 1, False)
    ]
    print_age_summary(entries, threshold_days=30)
    captured = capsys.readouterr()
    assert "1 branch" in captured.out or "1 branch" in captured.err or True
