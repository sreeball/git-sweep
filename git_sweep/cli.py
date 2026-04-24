"""Command-line interface for git-sweep."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from git_sweep.cleaner import delete_local_branch, delete_remote_branch, summary
from git_sweep.config import SweepConfig, load_config
from git_sweep.repo_scanner import get_merged_branches, is_git_repo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-sweep",
        description="Clean up merged branches and stale remotes across repositories.",
    )
    parser.add_argument(
        "repos",
        nargs="*",
        metavar="REPO",
        help="Repository paths to sweep (overrides config file).",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to a .git-sweep.toml config file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Print actions without executing them (overrides config).",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Actually perform deletions (overrides config).",
    )
    parser.add_argument(
        "--delete-remote",
        action="store_true",
        default=None,
        help="Also remove remote-tracking branches.",
    )
    parser.add_argument(
        "--remote",
        default=None,
        metavar="NAME",
        help="Remote name to target (default: origin).",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg: SweepConfig = load_config(args.config)

    # CLI flags override config file values
    if args.dry_run is not None:
        cfg.dry_run = args.dry_run
    if args.delete_remote is not None:
        cfg.delete_remote = args.delete_remote
    if args.remote is not None:
        cfg.remote_name = args.remote

    repo_paths = args.repos or cfg.repos or [str(Path.cwd())]

    all_results = []
    for repo_path in repo_paths:
        if not is_git_repo(repo_path):
            print(f"[SKIP] {repo_path} is not a git repository.", file=sys.stderr)
            continue

        scan_result = get_merged_branches(repo_path, cfg.remote_name)
        branches = [
            b for b in scan_result.branches if not cfg.is_protected(b.name)
        ]

        for branch in branches:
            if cfg.dry_run:
                print(f"[DRY-RUN] Would delete local branch '{branch.name}' in {repo_path}")
            else:
                result = delete_local_branch(repo_path, branch.name)
                all_results.append(result)
                if cfg.delete_remote:
                    r_result = delete_remote_branch(
                        repo_path, cfg.remote_name, branch.name
                    )
                    all_results.append(r_result)

    if not cfg.dry_run and all_results:
        print(summary(all_results))

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
