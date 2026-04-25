"""CLI helpers for the author-filter sub-command."""
from __future__ import annotations

import argparse
from typing import List

from git_sweep.walk import collect_repos
from git_sweep.repo_scanner import get_merged_branches
from git_sweep.author_filter import filter_by_author
from git_sweep.author_report import (
    format_author_text,
    format_author_json,
    print_author_summary,
)


def add_author_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "author",
        help="List merged branches filtered by author name or email.",
    )
    p.add_argument("pattern", help="Author name/email substring to match (case-insensitive).")
    p.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    p.add_argument("--max-depth", type=int, default=3, help="Max directory depth to search.")
    p.add_argument("--base", default="main", help="Base branch for merged detection (default: main).")
    p.add_argument("--json", dest="output_json", action="store_true", help="Output JSON.")
    p.set_defaults(func=run_author_command)


def run_author_command(args: argparse.Namespace) -> int:
    repos: List[str] = collect_repos(args.root, max_depth=args.max_depth)
    if not repos:
        print("No git repositories found.")
        return 0

    results = []
    for repo_path in repos:
        scan = get_merged_branches(repo_path, base_branch=args.base)
        af_result = filter_by_author(scan, pattern=args.pattern)
        results.append(af_result)

    if args.output_json:
        print(format_author_json(results, pattern=args.pattern))
    else:
        print(format_author_text(results, pattern=args.pattern))
        print()
        print_author_summary(results, pattern=args.pattern)

    return 0
