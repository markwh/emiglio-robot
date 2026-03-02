"""Git worktree, merge, and rebase helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from emiglio_pm.manifest import Manifest, find_repo_root


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    """Run a git command, optionally printing it for visibility."""
    if not quiet:
        print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def _is_conda_venv(worktree: Path) -> bool:
    """Check if a worktree's .venv is conda-poisoned."""
    python = worktree / ".venv" / "bin" / "python"
    if not python.exists():
        return False
    try:
        result = subprocess.run(
            [str(python), "-c", "import sys; print(sys.prefix)"],
            capture_output=True, text=True, check=True,
        )
        return "conda" in result.stdout.lower() or "miniforge" in result.stdout.lower()
    except subprocess.CalledProcessError:
        return False


def worktree_path(manifest: Manifest, name: str, repo_root: Path | None = None) -> Path:
    """Get the filesystem path for a worktree."""
    if repo_root is None:
        repo_root = find_repo_root()
    return repo_root / manifest.project.worktree_root / name


def worktree_exists(manifest: Manifest, name: str, repo_root: Path | None = None) -> bool:
    """Check if a worktree directory exists."""
    return worktree_path(manifest, name, repo_root).exists()


def is_dirty(worktree: Path) -> bool:
    """Check if a worktree has uncommitted changes."""
    result = _run(["git", "status", "--porcelain"], cwd=worktree, check=False, quiet=True)
    return bool(result.stdout.strip())


def current_branch(cwd: Path | None = None) -> str:
    """Get the current branch name."""
    result = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, quiet=True)
    return result.stdout.strip()


def latest_commit(cwd: Path | None = None) -> str:
    """Get the latest commit (short hash + subject)."""
    result = _run(["git", "log", "-1", "--oneline"], cwd=cwd, quiet=True)
    return result.stdout.strip()


def create_worktree(manifest: Manifest, name: str, repo_root: Path | None = None) -> Path:
    """Create a git worktree for a workstream."""
    if repo_root is None:
        repo_root = find_repo_root()

    ws = manifest.workstreams[name]
    wt_path = worktree_path(manifest, name, repo_root)

    if wt_path.exists():
        print(f"Worktree already exists: {wt_path}")
        return wt_path

    # Check if branch exists
    result = _run(
        ["git", "rev-parse", "--verify", ws.branch],
        cwd=repo_root, check=False,
    )
    if result.returncode == 0:
        # Branch exists — add worktree on existing branch
        _run(["git", "worktree", "add", str(wt_path), ws.branch], cwd=repo_root)
    else:
        # Branch doesn't exist — create from base branch
        _run(
            ["git", "worktree", "add", "-b", ws.branch, str(wt_path), manifest.project.base_branch],
            cwd=repo_root,
        )

    print(f"Created worktree: {wt_path} (branch: {ws.branch})")
    return wt_path


def merge_workstream(manifest: Manifest, name: str, repo_root: Path | None = None) -> None:
    """Merge a workstream branch into the base branch."""
    if repo_root is None:
        repo_root = find_repo_root()

    ws = manifest.workstreams[name]
    base = manifest.project.base_branch

    # Verify we're on the base branch
    branch = current_branch(repo_root)
    if branch != base:
        print(f"Error: must be on '{base}' to merge (currently on '{branch}')")
        sys.exit(1)

    # Show what will be merged
    result = _run(
        ["git", "log", f"{base}..{ws.branch}", "--oneline"],
        cwd=repo_root,
    )
    commits = result.stdout.strip()
    if not commits:
        print(f"Nothing to merge from {ws.branch}")
        return

    print(f"\nCommits to merge from {ws.branch}:")
    print(commits)
    print()

    _run(
        ["git", "merge", ws.branch, "--no-ff", "-m", f"Merge {ws.branch}: {ws.summary}"],
        cwd=repo_root,
    )
    print(f"Merged {ws.branch} into {base}")


def rebase_all(manifest: Manifest, repo_root: Path | None = None) -> None:
    """Rebase all worktree branches onto the base branch."""
    if repo_root is None:
        repo_root = find_repo_root()

    base = manifest.project.base_branch

    for name, ws in manifest.workstreams.items():
        wt = worktree_path(manifest, name, repo_root)
        if not wt.exists():
            print(f"[{name}] Worktree not found at {wt}, skipping")
            continue

        print(f"\n[{name}] Rebasing {ws.branch} onto {base}...")

        dirty = is_dirty(wt)
        if dirty:
            print(f"  Stashing uncommitted changes...")
            _run(["git", "stash", "push", "-m", "emiglio-pm rebase stash"], cwd=wt)

        result = _run(["git", "rebase", base], cwd=wt, check=False)
        if result.returncode != 0:
            print(f"  Rebase failed! Aborting...")
            print(f"  stderr: {result.stderr.strip()}")
            _run(["git", "rebase", "--abort"], cwd=wt, check=False)
            if dirty:
                _run(["git", "stash", "pop"], cwd=wt, check=False)
            continue

        if dirty:
            print(f"  Restoring stashed changes...")
            _run(["git", "stash", "pop"], cwd=wt, check=False)

        print(f"  Done.")


def status_all(manifest: Manifest, repo_root: Path | None = None) -> list[dict]:
    """Get status info for all worktrees."""
    if repo_root is None:
        repo_root = find_repo_root()

    results = []
    for name, ws in manifest.workstreams.items():
        wt = worktree_path(manifest, name, repo_root)
        info: dict = {
            "name": name,
            "branch": ws.branch,
            "exists": wt.exists(),
            "path": str(wt),
        }

        if wt.exists():
            info["dirty"] = is_dirty(wt)
            info["conda_venv"] = _is_conda_venv(wt)
            info["worktree_md"] = (wt / "WORKTREE.md").exists()
            info["latest_commit"] = latest_commit(wt)
        else:
            info["dirty"] = False
            info["conda_venv"] = False
            info["worktree_md"] = False
            info["latest_commit"] = ""

        results.append(info)

    return results
