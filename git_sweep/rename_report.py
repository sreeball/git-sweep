"""Formatting helpers for rename-detection results."""
from __future__ import annotations

import json
from typing import List

from git_sweep.branch_rename_detector import RenameDetectionResult
from git_sweep.output import print_info, print_warning


def format_rename_text(results: List[RenameDetectionResult], *, verbose: bool = False) -> str:
    lines: list[str] = []
    total = sum(len(r.candidates) for r in results)
    lines.append(f"Rename candidates found: {total}")
    for res in results:
        if res.error:
            lines.append(f"  [{res.repo_path}] ERROR: {res.error}")
            continue
        if not res.candidates:
            if verbose:
                lines.append(f"  [{res.repo_path}] no rename candidates")
            continue
        lines.append(f"  {res.repo_path}")
        for c in res.candidates:
            sim_pct = f"{c.similarity * 100:.0f}%"
            tip = f" tip={c.tip_commit[:8]}" if c.tip_commit else ""
            lines.append(
                f"    {c.old_branch!r:40s} -> {c.new_branch!r}  "
                f"(similarity {sim_pct}{tip})"
            )
    return "\n".join(lines)


def format_rename_json(results: List[RenameDetectionResult]) -> str:
    payload = []
    for res in results:
        payload.append(
            {
                "repo": res.repo_path,
                "error": res.error,
                "candidates": [
                    {
                        "old_branch": c.old_branch,
                        "new_branch": c.new_branch,
                        "similarity": c.similarity,
                        "tip_commit": c.tip_commit,
                    }
                    for c in res.candidates
                ],
            }
        )
    return json.dumps(payload, indent=2)


def print_rename_summary(results: List[RenameDetectionResult]) -> None:
    """Print a concise rename-detection summary to stdout."""
    total = sum(len(r.candidates) for r in results)
    if total == 0:
        print_info("No rename candidates detected.")
        return
    print_warning(f"{total} potential branch rename(s) detected — review before deleting.")
    for res in results:
        for c in res.candidates:
            print_info(
                f"  {res.repo_path}: '{c.old_branch}' may have been renamed to '{c.new_branch}'"
            )
