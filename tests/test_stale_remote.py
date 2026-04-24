"""Tests for git_sweep.stale_remote."""

from unittest.mock import patch

import pytest

from git_sweep.stale_remote import (
    StaleRemoteInfo,
    StaleRemoteResult,
    get_stale_remotes,
    prune_stale_remotes,
)

REPO = "/fake/repo"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BRANCH_VV_WITH_GONE = """\
  main          abc1234 [origin/main] Latest commit
* feature-gone  def5678 [origin/feature-gone: gone] Old feature
  other-gone    bbb0000 [upstream/other-gone: gone] Another stale
  local-only    ccc1111 No tracking info
"""

BRANCH_VV_CLEAN = """\
  main          abc1234 [origin/main] Latest commit
* develop       def5678 [origin/develop] Active
"""


def _make_run_git(branch_vv_output: str):
    """Return a side_effect callable for _run_git."""

    def _run(args, path):
        if args == ["remote"]:
            return "origin\n", None
        if args[:2] == ["remote", "prune"]:
            return "", None
        if args == ["branch", "-vv"]:
            return branch_vv_output, None
        if args[:2] == ["branch", "-D"]:
            return "", None
        return "", None

    return _run


# ---------------------------------------------------------------------------
# get_stale_remotes
# ---------------------------------------------------------------------------


@patch("git_sweep.stale_remote._run_git")
def test_get_stale_remotes_detects_gone(mock_run):
    mock_run.side_effect = _make_run_git(BRANCH_VV_WITH_GONE)
    result = get_stale_remotes(REPO)

    assert isinstance(result, StaleRemoteResult)
    assert result.error is None
    refs = [i.ref for i in result.stale]
    assert "feature-gone" in refs
    assert "other-gone" in refs
    assert "main" not in refs
    assert "local-only" not in refs


@patch("git_sweep.stale_remote._run_git")
def test_get_stale_remotes_clean_repo(mock_run):
    mock_run.side_effect = _make_run_git(BRANCH_VV_CLEAN)
    result = get_stale_remotes(REPO)

    assert result.stale == []
    assert result.error is None


@patch("git_sweep.stale_remote._run_git")
def test_get_stale_remotes_remote_error(mock_run):
    mock_run.return_value = ("", "fatal: not a git repository")
    result = get_stale_remotes(REPO)

    assert result.error is not None
    assert result.stale == []


# ---------------------------------------------------------------------------
# prune_stale_remotes
# ---------------------------------------------------------------------------


@patch("git_sweep.stale_remote._run_git")
def test_prune_stale_remotes_dry_run_does_not_delete(mock_run):
    mock_run.side_effect = _make_run_git(BRANCH_VV_WITH_GONE)
    result = prune_stale_remotes(REPO, dry_run=True)

    # Branches discovered but NOT deleted — no -D call expected.
    delete_calls = [
        c for c in mock_run.call_args_list if c.args[0][:2] == ["branch", "-D"]
    ]
    assert len(delete_calls) == 0
    assert len(result.stale) == 2


@patch("git_sweep.stale_remote._run_git")
def test_prune_stale_remotes_live_deletes(mock_run):
    mock_run.side_effect = _make_run_git(BRANCH_VV_WITH_GONE)
    result = prune_stale_remotes(REPO, dry_run=False)

    delete_calls = [
        c for c in mock_run.call_args_list if c.args[0][:2] == ["branch", "-D"]
    ]
    assert len(delete_calls) == 2
    assert result.error is None
