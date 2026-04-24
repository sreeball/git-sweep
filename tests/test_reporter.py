"""Tests for git_sweep.reporter."""

from __future__ import annotations

import json

import pytest

from git_sweep.cleaner import CleanResult
from git_sweep.repo_scanner import BranchInfo, RepoScanResult
from git_sweep.reporter import SweepReport, format_json, format_text


@pytest.fixture()
def sample_report() -> SweepReport:
    branch = BranchInfo(name="feature/old", remote=None, last_commit="abc1234")
    scan = RepoScanResult(repo_path="/repos/myapp", merged_branches=[branch])
    clean = CleanResult(
        repo_path="/repos/myapp",
        branch="feature/old",
        deleted=True,
        remote=False,
        error=None,
    )
    return SweepReport(scan_results=[scan], clean_results=[clean], dry_run=False)


def test_totals(sample_report: SweepReport) -> None:
    assert sample_report.total_repos == 1
    assert sample_report.repos_with_merged == 1
    assert sample_report.total_merged_found == 1
    assert sample_report.total_cleaned == 1
    assert sample_report.errors == []


def test_format_text_contains_repo(sample_report: SweepReport) -> None:
    text = format_text(sample_report)
    assert "/repos/myapp" in text
    assert "feature/old" in text
    assert "Branches deleted" in text


def test_format_text_dry_run() -> None:
    report = SweepReport(dry_run=True)
    text = format_text(report)
    assert "DRY RUN" in text
    assert "Branches deleted" not in text


def test_format_json_valid(sample_report: SweepReport) -> None:
    raw = format_json(sample_report)
    data = json.loads(raw)
    assert data["total_repos"] == 1
    assert data["total_merged_found"] == 1
    assert data["total_cleaned"] == 1
    assert data["repos"][0]["path"] == "/repos/myapp"


def test_errors_aggregated() -> None:
    scan = RepoScanResult(repo_path="/bad", merged_branches=[], error="not a repo")
    clean = CleanResult(
        repo_path="/repos/x", branch="feat", deleted=False, remote=False, error="permission denied"
    )
    report = SweepReport(scan_results=[scan], clean_results=[clean])
    assert len(report.errors) == 2
    assert any("not a repo" in e for e in report.errors)
    assert any("permission denied" in e for e in report.errors)
