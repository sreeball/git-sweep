"""CLI sub-command: tag-sweep — find and remove stale local tags."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from git_sweep.tag_cleaner import TagCleanResult, delete_stale_tags, get_stale_tags
from git_sweep.tag_report import format_tag_json, format_tag_text, print_tag_summary
from git_sweep.walk import collect_repos


def add_tag_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "tag-sweep",
        help="Find and delete stale local tags not present on any remote.",
    )
    p.add_argument("path", nargs="?", default=".", help="Root path to scan (default: .)")
    p.add_argument("--delete", action="store_true", help="Actually delete stale tags (default: dry-run)")
    p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    p.add_argument("--max-depth", type=int, default=3, help="Max directory depth to scan")
    p.set_defaults(func=run_tag_command)


def run_tag_command(args: argparse.Namespace) -> None:
    root = Path(args.path).resolve()
    dry_run = not args.delete
    repos = collect_repos(root, max_depth=args.max_depth)

    results: List[TagCleanResult] = []
    for repo_path in repos:
        scan = get_stale_tags(repo_path)
        if scan.stale_tags and not scan.error:
            delete_stale_tags(scan, dry_run=dry_run)
        results.append(scan)

    if args.json_output:
        print(format_tag_json(results))
    else:
        print(format_tag_text(results, dry_run=dry_run))
        print()
        print_tag_summary(results, dry_run=dry_run)
