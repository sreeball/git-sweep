"""Formatting helpers for tag-cleaner results."""
from __future__ import annotations

import json
from typing import List

from git_sweep.output import print_info, print_success, print_warning
from git_sweep.tag_cleaner import TagCleanResult


def format_tag_text(results: List[TagCleanResult], dry_run: bool = True) -> str:
    lines: List[str] = []
    prefix = "[dry-run] " if dry_run else ""
    for r in results:
        lines.append(f"repo: {r.repo_path}")
        if r.error:
            lines.append(f"  error: {r.error}")
            continue
        if not r.stale_tags:
            lines.append("  no stale tags found")
            continue
        for tag in r.stale_tags:
            deleted = tag.name in r.deleted
            status = f"{prefix}deleted" if deleted else "stale"
            lines.append(f"  [{status}] {tag.name}  {tag.sha[:8] if tag.sha else ''}")
        if r.errors:
            for e in r.errors:
                lines.append(f"  error: {e}")
    return "\n".join(lines)


def format_tag_json(results: List[TagCleanResult]) -> str:
    data = []
    for r in results:
        data.append({
            "repo": str(r.repo_path),
            "stale_tags": [{"name": t.name, "sha": t.sha} for t in r.stale_tags],
            "deleted": r.deleted,
            "errors": r.errors,
            "error": r.error,
        })
    return json.dumps(data, indent=2)


def print_tag_summary(results: List[TagCleanResult], dry_run: bool = True) -> None:
    total_stale = sum(len(r.stale_tags) for r in results)
    total_deleted = sum(len(r.deleted) for r in results)

    if total_stale == 0:
        print_success("No stale tags found.")
        return

    print_info(f"Stale tags found: {total_stale}")
    if dry_run:
        print_warning(f"Dry-run: {total_deleted} tag(s) would be deleted.")
    else:
        print_success(f"Deleted {total_deleted} tag(s).")
