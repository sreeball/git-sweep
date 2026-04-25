"""Tests for git_sweep.author_report."""
from __future__ import annotations

import json

from git_sweep.repo_scanner import BranchInfo
from git_sweep.author_filter import AuthorFilterResult
from git_sweep.author_report import format_author_text, format_author_json, print_author_summary


def _result(repo, matched=(), skipped=(), error=None):
    return AuthorFilterResult(
        repo_path=repo,
        matched=[BranchInfo(name=b) for b in matched],
        skipped=[BranchInfo(name=b) for b in skipped],
        error=error,
    )


# ---------------------------------------------------------------------------
# format_author_text
# ---------------------------------------------------------------------------

def test_format_text_contains_pattern():
    text = format_author_text([], pattern="alice")
    assert "alice" in text


def test_format_text_shows_matched_branch():
    r = _result("/repo", matched=["feature/x"])
    text = format_author_text([r], pattern="alice")
    assert "feature/x" in text


def test_format_text_shows_no_match_message():
    r = _result("/repo")
    text = format_author_text([r], pattern="alice")
    assert "No matching" in text


def test_format_text_shows_error():
    r = _result("/repo", error="git exploded")
    text = format_author_text([r], pattern="alice")
    assert "git exploded" in text


# ---------------------------------------------------------------------------
# format_author_json
# ---------------------------------------------------------------------------

def test_format_json_valid():
    r = _result("/repo", matched=["feat/a"], skipped=["feat/b"])
    raw = format_author_json([r], pattern="alice")
    data = json.loads(raw)
    assert data["author_pattern"] == "alice"
    assert data["repos"][0]["matched"] == ["feat/a"]
    assert data["repos"][0]["skipped"] == ["feat/b"]


def test_format_json_error_repo():
    r = _result("/bad", error="oops")
    data = json.loads(format_author_json([r], pattern="x"))
    assert data["repos"][0]["error"] == "oops"


# ---------------------------------------------------------------------------
# print_author_summary (smoke test — just ensure no exceptions)
# ---------------------------------------------------------------------------

def test_print_author_summary_runs(capsys):
    results = [
        _result("/r1", matched=["a", "b"]),
        _result("/r2"),
        _result("/r3", error="fail"),
    ]
    print_author_summary(results, pattern="dev")
    captured = capsys.readouterr()
    assert "dev" in captured.out
