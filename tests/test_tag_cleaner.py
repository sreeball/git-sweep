"""Tests for git_sweep.tag_cleaner."""
from __future__ import annotations

import types
from pathlib import Path
from unittest.mock import patch

import pytest

from git_sweep.tag_cleaner import (
    StaleTagInfo,
    TagCleanResult,
    delete_stale_tags,
    get_stale_tags,
)

_REPO = Path("/fake/repo")


def _proc(stdout: str = "", stderr: str = "", returncode: int = 0):
    p = types.SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    return p


def _make_run(responses: list):
    calls = iter(responses)

    def _run_git(cmd, cwd=None):
        return next(calls)

    return _run_git


# ---------------------------------------------------------------------------
# get_stale_tags
# ---------------------------------------------------------------------------

def test_get_stale_tags_no_local_tags():
    runner = _make_run([_proc(stdout=""), _proc(stdout="")])
    with patch("git_sweep.tag_cleaner._run_git", runner):
        result = get_stale_tags(_REPO)
    assert result.stale_tags == []
    assert result.error is None


def test_get_stale_tags_detects_stale():
    local_out = "v1.0\nv2.0\n"
    remote_out = "abc123\trefs/tags/v1.0\n"
    sha_out = "deadbeef1234"
    runner = _make_run([
        _proc(stdout=local_out),
        _proc(stdout=remote_out),
        _proc(stdout=sha_out),  # rev-list for v2.0
    ])
    with patch("git_sweep.tag_cleaner._run_git", runner):
        result = get_stale_tags(_REPO)
    assert len(result.stale_tags) == 1
    assert result.stale_tags[0].name == "v2.0"
    assert result.stale_tags[0].sha == sha_out


def test_get_stale_tags_remote_error():
    runner = _make_run([
        _proc(stdout="v1.0\n"),
        _proc(returncode=1, stderr="remote error"),
    ])
    with patch("git_sweep.tag_cleaner._run_git", runner):
        result = get_stale_tags(_REPO)
    assert result.error == "remote error"
    assert result.stale_tags == []


def test_get_stale_tags_local_error():
    runner = _make_run([_proc(returncode=128, stderr="not a git repo")])
    with patch("git_sweep.tag_cleaner._run_git", runner):
        result = get_stale_tags(_REPO)
    assert result.error == "not a git repo"


# ---------------------------------------------------------------------------
# delete_stale_tags
# ---------------------------------------------------------------------------

def test_delete_stale_tags_dry_run():
    result = TagCleanResult(
        repo_path=_REPO,
        stale_tags=[StaleTagInfo(name="old-tag", sha="abc")],
    )
    delete_stale_tags(result, dry_run=True)
    assert "old-tag" in result.deleted


def test_delete_stale_tags_live():
    result = TagCleanResult(
        repo_path=_REPO,
        stale_tags=[StaleTagInfo(name="old-tag", sha="abc")],
    )
    runner = _make_run([_proc(stdout="Deleted tag 'old-tag'")])
    with patch("git_sweep.tag_cleaner._run_git", runner):
        delete_stale_tags(result, dry_run=False)
    assert "old-tag" in result.deleted
    assert result.errors == []


def test_delete_stale_tags_live_error():
    result = TagCleanResult(
        repo_path=_REPO,
        stale_tags=[StaleTagInfo(name="bad-tag", sha="")],
    )
    runner = _make_run([_proc(returncode=1, stderr="tag not found")])
    with patch("git_sweep.tag_cleaner._run_git", runner):
        delete_stale_tags(result, dry_run=False)
    assert result.deleted == []
    assert any("bad-tag" in e for e in result.errors)
