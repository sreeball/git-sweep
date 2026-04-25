"""Snapshot sub-commands: list, show, and the new *diff-stat* sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from git_sweep.snapshot import list_snapshots, load_snapshot
from git_sweep.output import print_error, print_info, print_success
from git_sweep.diff_stat import collect_diff_stats


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    snap = subparsers.add_parser("snapshot", help="Manage sweep snapshots")
    snap_sub = snap.add_subparsers(dest="snap_cmd")

    snap_sub.add_parser("list", help="List saved snapshots")

    show_p = snap_sub.add_parser("show", help="Show a snapshot")
    show_p.add_argument("name", help="Snapshot filename or tag")
    show_p.add_argument("--json", dest="as_json", action="store_true")

    diff_p = snap_sub.add_parser("diff-stat", help="Show ahead/behind stats for branches in a snapshot")
    diff_p.add_argument("name", help="Snapshot filename or tag")
    diff_p.add_argument("--base", default="main", help="Base branch for comparison (default: main)")


def run_snapshot_command(args: argparse.Namespace) -> int:
    cmd = getattr(args, "snap_cmd", None)
    if cmd == "list":
        return _cmd_list()
    if cmd == "show":
        return _cmd_show(args)
    if cmd == "diff-stat":
        return _cmd_diff_stat(args)
    print_error("No snapshot sub-command given. Try: list, show, diff-stat")
    return 1


def _cmd_list() -> int:
    snapshots: List[str] = list_snapshots()
    if not snapshots:
        print_info("No snapshots found.")
        return 0
    for name in snapshots:
        print_info(name)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    report = load_snapshot(args.name)
    if report is None:
        print_error(f"Snapshot not found: {args.name}")
        return 1
    if getattr(args, "as_json", False):
        print(json.dumps(report, indent=2))
    else:
        for repo, data in report.get("repos", {}).items():
            print_info(f"[{repo}]")
            for branch in data.get("merged", []):
                print(f"  {branch}")
    return 0


def _cmd_diff_stat(args: argparse.Namespace) -> int:
    report = load_snapshot(args.name)
    if report is None:
        print_error(f"Snapshot not found: {args.name}")
        return 1

    base: str = args.base
    any_errors = False

    for repo_path, data in report.get("repos", {}).items():
        branches: List[str] = data.get("merged", [])
        if not branches:
            continue

        print_info(f"\n{repo_path}  (base: {base})")
        result = collect_diff_stats(repo_path, branches, base=base)

        for stat in result.stats:
            if stat.error:
                print_error(f"  {stat.branch}: {stat.error}")
                any_errors = True
            else:
                author_info = f"{stat.last_author}, {stat.last_commit_date}" if stat.last_author else "n/a"
                print_success(
                    f"  {stat.branch:<40}  "
                    f"behind={stat.commits_behind:>3}  ahead={stat.commits_ahead:>3}  "
                    f"last: {author_info}"
                )

    return 1 if any_errors else 0
