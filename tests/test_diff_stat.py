"""Tests for git_sweep.diff_stat."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_sweep.diff_stat import (
    BranchDiffStat,
    collect_diff_stats,
    get_branch_diff_stat,
)


def _make_proc(stdout: str = "", stderr: str = "", returncode: int = 0):
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


class TestGetBranchDiffStat:
    def test_parses_ahead_behind(self):
        rev_proc = _make_proc(stdout="3\t7\n")
        log_proc = _make_proc(stdout="Alice|2024-01-15 10:00:00 +0000")

        with patch("git_sweep.diff_stat._run_git", side_effect=[rev_proc, log_proc]):
            stat = get_branch_diff_stat("/repo", "feature/x", base="main")

        assert stat.branch == "feature/x"
        assert stat.commits_behind == 3
        assert stat.commits_ahead == 7
        assert stat.last_author == "Alice"
        assert stat.last_commit_date == "2024-01-15 10:00:00 +0000"
        assert stat.error is None

    def test_rev_list_error_sets_error_field(self):
        rev_proc = _make_proc(returncode=128, stderr="unknown revision")

        with patch("git_sweep.diff_stat._run_git", return_value=rev_proc):
            stat = get_branch_diff_stat("/repo", "bad-branch", base="main")

        assert stat.error == "unknown revision"
        assert stat.commits_behind == 0
        assert stat.commits_ahead == 0

    def test_log_failure_leaves_author_none(self):
        rev_proc = _make_proc(stdout="0\t2\n")
        log_proc = _make_proc(returncode=128, stderr="fatal")

        with patch("git_sweep.diff_stat._run_git", side_effect=[rev_proc, log_proc]):
            stat = get_branch_diff_stat("/repo", "feature/y", base="main")

        assert stat.last_author is None
        assert stat.last_commit_date is None
        assert stat.commits_ahead == 2

    def test_log_without_pipe_leaves_author_none(self):
        rev_proc = _make_proc(stdout="1\t1\n")
        log_proc = _make_proc(stdout="no-separator-here")

        with patch("git_sweep.diff_stat._run_git", side_effect=[rev_proc, log_proc]):
            stat = get_branch_diff_stat("/repo", "feature/z")

        assert stat.last_author is None


class TestCollectDiffStats:
    def test_returns_stat_per_branch(self):
        def fake_run_git(cmd, cwd):
            if "rev-list" in cmd:
                return _make_proc(stdout="0\t1\n")
            return _make_proc(stdout="Bob|2024-03-01 09:00:00 +0000")

        with patch("git_sweep.diff_stat._run_git", side_effect=fake_run_git):
            result = collect_diff_stats("/repo", ["feat/a", "feat/b"])

        assert result.repo_path == "/repo"
        assert len(result.stats) == 2
        assert result.stats[0].branch == "feat/a"
        assert result.stats[1].branch == "feat/b"

    def test_empty_branch_list(self):
        result = collect_diff_stats("/repo", [])
        assert result.stats == []
        assert result.error is None
