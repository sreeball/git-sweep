"""Reporting and output formatting for git-sweep results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import json

from git_sweep.cleaner import CleanResult, total_deleted, summary
from git_sweep.repo_scanner import RepoScanResult


@dataclass
class SweepReport:
    """Aggregated report across all scanned repositories."""

    scan_results: List[RepoScanResult] = field(default_factory=list)
    clean_results: List[CleanResult] = field(default_factory=list)
    dry_run: bool = True

    @property
    def total_repos(self) -> int:
        return len(self.scan_results)

    @property
    def repos_with_merged(self) -> int:
        return sum(1 for r in self.scan_results if r.merged_branches)

    @property
    def total_merged_found(self) -> int:
        return sum(len(r.merged_branches) for r in self.scan_results)

    @property
    def total_cleaned(self) -> int:
        return total_deleted(self.clean_results)

    @property
    def errors(self) -> List[str]:
        errs: List[str] = []
        for r in self.scan_results:
            if r.error:
                errs.append(f"{r.repo_path}: {r.error}")
        for c in self.clean_results:
            if c.error:
                errs.append(f"{c.repo_path}/{c.branch}: {c.error}")
        return errs


def format_text(report: SweepReport) -> str:
    """Render a human-readable text report."""
    lines: List[str] = []
    mode = "[DRY RUN] " if report.dry_run else ""
    lines.append(f"{mode}git-sweep report")
    lines.append("=" * 40)
    lines.append(f"Repos scanned : {report.total_repos}")
    lines.append(f"Repos with merged branches: {report.repos_with_merged}")
    lines.append(f"Merged branches found : {report.total_merged_found}")
    if not report.dry_run:
        lines.append(f"Branches deleted : {report.total_cleaned}")
    lines.append("")

    for result in report.scan_results:
        if not result.merged_branches:
            continue
        lines.append(f"  {result.repo_path}")
        for branch in result.merged_branches:
            remote_tag = f" (remote: {branch.remote})" if branch.remote else ""
            lines.append(f"    - {branch.name}{remote_tag}")

    if report.errors:
        lines.append("")
        lines.append("Errors:")
        for err in report.errors:
            lines.append(f"  ! {err}")

    return "\n".join(lines)


def format_json(report: SweepReport) -> str:
    """Render a JSON report."""
    data = {
        "dry_run": report.dry_run,
        "total_repos": report.total_repos,
        "repos_with_merged": report.repos_with_merged,
        "total_merged_found": report.total_merged_found,
        "total_cleaned": report.total_cleaned,
        "errors": report.errors,
        "repos": [
            {
                "path": r.repo_path,
                "merged_branches": [
                    {"name": b.name, "remote": b.remote, "last_commit": b.last_commit}
                    for b in r.merged_branches
                ],
                "error": r.error,
            }
            for r in report.scan_results
        ],
    }
    return json.dumps(data, indent=2)
