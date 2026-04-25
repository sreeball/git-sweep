"""Tests for git_sweep.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from git_sweep.cleaner import CleanResult
from git_sweep.reporter import SweepReport
from git_sweep.snapshot import (
    list_snapshots,
    load_snapshot,
    save_snapshot,
    snapshot_path,
)


@pytest.fixture()
def minimal_report() -> SweepReport:
    result = CleanResult(
        repo_path=Path("/tmp/repo"),
        deleted_local=["feature/old"],
        deleted_remote=[],
        failed=[],
        dry_run=False,
    )
    return SweepReport(results=[result], dry_run=False)


def test_snapshot_path_contains_timestamp(tmp_path: Path) -> None:
    p = snapshot_path(directory=tmp_path)
    assert p.parent == tmp_path
    assert p.name.startswith("sweep-")
    assert p.suffix == ".json"


def test_snapshot_path_with_tag(tmp_path: Path) -> None:
    p = snapshot_path(directory=tmp_path, tag="ci")
    assert "-ci.json" in p.name


def test_save_snapshot_creates_file(tmp_path: Path, minimal_report: SweepReport) -> None:
    path = save_snapshot(minimal_report, directory=tmp_path)
    assert path.exists()


def test_save_snapshot_valid_json(tmp_path: Path, minimal_report: SweepReport) -> None:
    path = save_snapshot(minimal_report, directory=tmp_path)
    data = json.loads(path.read_text())
    assert "created_at" in data
    assert "dry_run" in data
    assert "data" in data


def test_save_snapshot_dry_run_flag(tmp_path: Path, minimal_report: SweepReport) -> None:
    minimal_report.dry_run = True
    path = save_snapshot(minimal_report, directory=tmp_path)
    data = json.loads(path.read_text())
    assert data["dry_run"] is True


def test_load_snapshot_roundtrip(tmp_path: Path, minimal_report: SweepReport) -> None:
    path = save_snapshot(minimal_report, directory=tmp_path)
    loaded = load_snapshot(path)
    assert loaded["data"]["total_repos"] == 1


def test_load_snapshot_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "nonexistent.json")


def test_list_snapshots_empty(tmp_path: Path) -> None:
    assert list_snapshots(tmp_path / "missing") == []


def test_list_snapshots_sorted_newest_first(
    tmp_path: Path, minimal_report: SweepReport
) -> None:
    p1 = save_snapshot(minimal_report, directory=tmp_path, tag="a")
    p2 = save_snapshot(minimal_report, directory=tmp_path, tag="b")
    result = list_snapshots(tmp_path)
    assert len(result) == 2
    # newest file name sorts last alphabetically (timestamps are ascending)
    assert result[0].name >= result[1].name
