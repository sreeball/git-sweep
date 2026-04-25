"""Formatting helpers for author-filter results."""
from __future__ import annotations

import json
from typing import List

from git_sweep.author_filter import AuthorFilterResult
from git_sweep.output import print_info, print_warning, print_success


def format_author_text(results: List[AuthorFilterResult], pattern: str) -> str:
    lines: List[str] = []
    lines.append(f"Author filter: '{pattern}'")
    lines.append("=" * 40)
    for r in results:
        lines.append(f"\nRepo: {r.repo_path}")
        if r.error:
            lines.append(f"  ERROR: {r.error}")
            continue
        if not r.matched:
            lines.append("  No matching branches.")
        else:
            lines.append(f"  Matched ({len(r.matched)}):")
            for b in r.matched:
                lines.append(f"    - {b.name}")
        if r.skipped:
            lines.append(f"  Skipped ({len(r.skipped)}):")
            for b in r.skipped:
                lines.append(f"    - {b.name}")
    return "\n".join(lines)


def format_author_json(results: List[AuthorFilterResult], pattern: str) -> str:
    payload = {
        "author_pattern": pattern,
        "repos": [
            {
                "repo_path": r.repo_path,
                "error": r.error,
                "matched": [b.name for b in r.matched],
                "skipped": [b.name for b in r.skipped],
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)


def print_author_summary(
    results: List[AuthorFilterResult],
    pattern: str,
    use_color: bool = True,
) -> None:
    total_matched = sum(len(r.matched) for r in results)
    print_info(f"Author filter '{pattern}' — {total_matched} branch(es) matched across {len(results)} repo(s).")
    for r in results:
        if r.error:
            print_warning(f"  {r.repo_path}: {r.error}")
        elif r.matched:
            print_success(f"  {r.repo_path}: {len(r.matched)} matched")
        else:
            print_info(f"  {r.repo_path}: none matched")
