# git-sweep

> CLI tool to clean up merged branches and stale remotes across multiple repositories.

---

## Installation

```bash
pip install git-sweep
```

Or install from source:

```bash
pip install git+https://github.com/yourname/git-sweep.git
```

---

## Usage

Run `git-sweep` from any directory containing one or more git repositories:

```bash
# Preview branches that would be deleted (dry run)
git-sweep --dry-run

# Clean up merged branches across all repos in current directory
git-sweep --path ~/projects

# Remove stale remote-tracking references as well
git-sweep --path ~/projects --prune-remotes

# Target a specific base branch (default: main)
git-sweep --base develop
```

### Options

| Flag | Description |
|------|-------------|
| `--path` | Root directory to scan for repositories (default: `.`) |
| `--base` | Base branch to check merges against (default: `main`) |
| `--dry-run` | Preview changes without deleting anything |
| `--prune-remotes` | Also prune stale remote-tracking branches |
| `--force` | Skip confirmation prompts |

---

## Example Output

```
Scanning repositories in /home/user/projects...

[api-service]   Deleted: feature/login, fix/typo
[web-client]    Deleted: chore/cleanup, feature/dark-mode
[shared-lib]    Nothing to clean.

Done. Removed 4 branches across 3 repositories.
```

---

## License

This project is licensed under the [MIT License](LICENSE).