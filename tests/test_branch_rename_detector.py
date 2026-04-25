"""Tests for git_sweep.branch_rename_detector."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from git_sweep.branch_rename_detector import (
    RenameCandidate,
    RenameDetectionResult,
    _similarity,
    find_rename_candidates,
)

REPO = "/fake/repo"


def _make_run(stdout: str = "", returncode: int = 0):
    def _run_git(cmd, cwd=None, **kwargs):
        return SimpleNamespace(stdout=stdout, returncode=returncode)

    return _run_git


# ── unit: similarity helper ──────────────────────────────────────────────────

def test_similarity_identical():
    assert _similarity("feature/foo", "feature/foo") == 1.0


def test_similarity_different():
    assert _similarity("abc", "xyz") < 0.5


def test_similarity_partial():
    score = _similarity("feature/login", "feature/login-v2")
    assert 0.5 < score < 1.0


# ── find_rename_candidates ────────────────────────────────────────────────────

BRANCH_OUTPUT = (
    "main abc123\n"
    "feature/login-v2 deadbeef\n"
    "feature/login deadbeef\n"  # same tip as login-v2 → rename candidate
)


def test_detects_same_tip_commit():
    with patch("git_sweep.branch_rename_detector._run_git", _make_run(BRANCH_OUTPUT)):
        result = find_rename_candidates(
            REPO,
            merged_branches=["feature/login"],
        )
    assert result.error is None
    assert len(result.candidates) == 1
    c = result.candidates[0]
    assert c.old_branch == "feature/login"
    assert c.new_branch == "feature/login-v2"
    assert c.tip_commit == "deadbeef"


def test_detects_high_similarity_even_different_tip():
    branch_out = "main abc123\nfeature/login-renamed 111111\nfeature/login 222222\n"
    with patch("git_sweep.branch_rename_detector._run_git", _make_run(branch_out)):
        result = find_rename_candidates(
            REPO,
            merged_branches=["feature/login"],
            threshold=0.6,
        )
    assert any(c.old_branch == "feature/login" for c in result.candidates)


def test_no_candidates_when_no_similar_branches():
    branch_out = "main abc123\nzz-totally-unrelated 999999\nfeature/login deadbeef\n"
    with patch("git_sweep.branch_rename_detector._run_git", _make_run(branch_out)):
        result = find_rename_candidates(
            REPO,
            merged_branches=["feature/login"],
            threshold=0.95,
        )
    assert result.candidates == []


def test_error_on_git_failure():
    def boom(cmd, cwd=None, **kwargs):
        raise RuntimeError("git not found")

    with patch("git_sweep.branch_rename_detector._run_git", boom):
        result = find_rename_candidates(REPO, merged_branches=["feature/x"])
    assert result.error is not None
    assert "git not found" in result.error


def test_empty_merged_list_returns_no_candidates():
    with patch("git_sweep.branch_rename_detector._run_git", _make_run(BRANCH_OUTPUT)):
        result = find_rename_candidates(REPO, merged_branches=[])
    assert result.candidates == []
