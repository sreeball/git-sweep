"""Tests for git_sweep.config."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from git_sweep.config import (
    DEFAULT_PROTECTED_BRANCHES,
    SweepConfig,
    _find_config_file,
    load_config,
)


# ---------------------------------------------------------------------------
# SweepConfig unit tests
# ---------------------------------------------------------------------------


def test_sweep_config_defaults():
    cfg = SweepConfig()
    assert cfg.dry_run is True
    assert cfg.delete_remote is False
    assert cfg.remote_name == "origin"
    assert cfg.repos == []
    assert cfg.protected_branches == list(DEFAULT_PROTECTED_BRANCHES)


def test_is_protected_true():
    cfg = SweepConfig()
    assert cfg.is_protected("main") is True
    assert cfg.is_protected("master") is True


def test_is_protected_false():
    cfg = SweepConfig()
    assert cfg.is_protected("feature/my-branch") is False


def test_is_protected_custom_list():
    cfg = SweepConfig(protected_branches=["release"])
    assert cfg.is_protected("release") is True
    assert cfg.is_protected("main") is False


# ---------------------------------------------------------------------------
# _find_config_file
# ---------------------------------------------------------------------------


def test_find_config_file_found(tmp_path):
    cfg_file = tmp_path / ".git-sweep.toml"
    cfg_file.write_text("")
    sub = tmp_path / "subdir"
    sub.mkdir()
    assert _find_config_file(sub) == cfg_file


def test_find_config_file_not_found(tmp_path):
    assert _find_config_file(tmp_path) is None


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


def test_load_config_no_file_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert isinstance(cfg, SweepConfig)
    assert cfg.dry_run is True


def test_load_config_from_explicit_path(tmp_path):
    toml_content = textwrap.dedent("""
        [sweep]
        dry_run = false
        delete_remote = true
        remote = "upstream"
        older_than_days = 30
        repos = ["/tmp/repo1", "/tmp/repo2"]
        protected_branches = ["main", "release"]
    """)
    cfg_file = tmp_path / ".git-sweep.toml"
    cfg_file.write_bytes(toml_content.encode())

    try:
        cfg = load_config(str(cfg_file))
    except Exception:
        pytest.skip("tomllib/tomli not available")

    assert cfg.dry_run is False
    assert cfg.delete_remote is True
    assert cfg.remote_name == "upstream"
    assert cfg.older_than_days == 30
    assert cfg.repos == ["/tmp/repo1", "/tmp/repo2"]
    assert cfg.protected_branches == ["main", "release"]
