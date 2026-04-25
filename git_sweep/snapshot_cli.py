"""CLI helpers for the `git-sweep snapshot` sub-commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from git_sweep.output import print_error, print_info, print_success
from git_sweep.snapshot import DEFAULT_SNAPSHOT_DIR, list_snapshots, load_snapshot


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *snapshot* sub-command onto *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "snapshot",
        help="Manage saved sweep snapshots.",
    )
    snap_sub = parser.add_subparsers(dest="snap_cmd", required=True)

    # list
    list_p = snap_sub.add_parser("list", help="List saved snapshots.")
    list_p.add_argument(
        "--dir",
        default=str(DEFAULT_SNAPSHOT_DIR),
        help="Directory containing snapshots (default: %(default)s).",
    )

    # show
    show_p = snap_sub.add_parser("show", help="Print a snapshot as JSON.")
    show_p.add_argument("file", help="Path to the snapshot file.")


def run_snapshot_command(args: argparse.Namespace) -> int:
    """Dispatch snapshot sub-commands; return exit code."""
    if args.snap_cmd == "list":
        return _cmd_list(Path(args.dir))
    if args.snap_cmd == "show":
        return _cmd_show(Path(args.file))
    print_error(f"Unknown snapshot command: {args.snap_cmd}")
    return 1


def _cmd_list(directory: Path) -> int:
    snapshots = list_snapshots(directory)
    if not snapshots:
        print_info("No snapshots found.")
        return 0
    print_info(f"Snapshots in {directory}:")
    for path in snapshots:
        print_success(f"  {path.name}")
    return 0


def _cmd_show(path: Path) -> int:
    try:
        data = load_snapshot(path)
    except FileNotFoundError as exc:
        print_error(str(exc))
        return 1
    import json

    print(json.dumps(data, indent=2))
    return 0
