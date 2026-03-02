"""CLI entry point for emiglio-pm."""

from __future__ import annotations

import argparse
import sys

from emiglio_pm.manifest import find_repo_root, load_manifest


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of all worktrees."""
    from emiglio_pm.git_ops import status_all

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)
    results = status_all(manifest, repo_root)

    print(f"Base branch: {manifest.project.base_branch}")
    print(f"Worktree root: {manifest.project.worktree_root}")
    print()

    for info in results:
        exists_mark = "Y" if info["exists"] else "-"
        dirty_mark = "dirty" if info["dirty"] else "clean"
        conda_mark = "CONDA!" if info["conda_venv"] else ""
        wt_md_mark = "Y" if info["worktree_md"] else "-"

        status = f"[{exists_mark}]"
        if info["exists"]:
            status += f" {dirty_mark}"
            if conda_mark:
                status += f" {conda_mark}"
            status += f" | WORKTREE.md: {wt_md_mark}"
            status += f" | {info['latest_commit']}"

        print(f"  {info['name']:15s} ({info['branch']:25s}) {status}")


def cmd_create(args: argparse.Namespace) -> None:
    """Create a worktree for a workstream."""
    from emiglio_pm.git_ops import create_worktree
    from emiglio_pm.worktree_md import sync_worktree_md

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)

    name = args.name
    if name not in manifest.workstreams:
        print(f"Unknown workstream: {name}")
        print(f"Available: {', '.join(manifest.workstreams)}")
        sys.exit(1)

    create_worktree(manifest, name, repo_root)
    out = sync_worktree_md(manifest, name, repo_root)
    print(f"Generated {out}")


def cmd_sync(args: argparse.Namespace) -> None:
    """Regenerate WORKTREE.md in a worktree."""
    from emiglio_pm.worktree_md import sync_worktree_md

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)

    name = args.name
    if name not in manifest.workstreams:
        print(f"Unknown workstream: {name}")
        print(f"Available: {', '.join(manifest.workstreams)}")
        sys.exit(1)

    out = sync_worktree_md(manifest, name, repo_root)
    print(f"Generated {out}")


def cmd_sync_all(args: argparse.Namespace) -> None:
    """Regenerate WORKTREE.md in all worktrees."""
    from emiglio_pm.git_ops import worktree_exists
    from emiglio_pm.worktree_md import sync_worktree_md

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)

    for name in manifest.workstreams:
        if worktree_exists(manifest, name, repo_root):
            out = sync_worktree_md(manifest, name, repo_root)
            print(f"Generated {out}")
        else:
            print(f"Skipping {name} (worktree not found)")


def cmd_merge(args: argparse.Namespace) -> None:
    """Merge a workstream branch into base."""
    from emiglio_pm.git_ops import merge_workstream

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)

    name = args.name
    if name not in manifest.workstreams:
        print(f"Unknown workstream: {name}")
        print(f"Available: {', '.join(manifest.workstreams)}")
        sys.exit(1)

    merge_workstream(manifest, name, repo_root)


def cmd_shell_init(args: argparse.Namespace) -> None:
    """Print bash snippet for per-worktree terminal colors."""
    from emiglio_pm.shell_init import generate_shell_init

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)
    print(generate_shell_init(manifest, repo_root))


def cmd_rebase_all(args: argparse.Namespace) -> None:
    """Rebase all worktree branches onto base."""
    from emiglio_pm.git_ops import rebase_all

    repo_root = find_repo_root()
    manifest = load_manifest(repo_root)
    rebase_all(manifest, repo_root)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="emiglio-pm",
        description="Emiglio workstream management CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show all worktree status")

    p_create = sub.add_parser("create", help="Create a worktree")
    p_create.add_argument("name", help="Workstream name")

    p_sync = sub.add_parser("sync", help="Regenerate WORKTREE.md in a worktree")
    p_sync.add_argument("name", help="Workstream name")

    sub.add_parser("sync-all", help="Regenerate WORKTREE.md in all worktrees")

    p_merge = sub.add_parser("merge", help="Merge workstream into base branch")
    p_merge.add_argument("name", help="Workstream name")

    sub.add_parser("rebase-all", help="Rebase all worktree branches onto base")

    sub.add_parser("shell-init", help="Print bash snippet for terminal colors")

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "create": cmd_create,
        "sync": cmd_sync,
        "sync-all": cmd_sync_all,
        "merge": cmd_merge,
        "rebase-all": cmd_rebase_all,
        "shell-init": cmd_shell_init,
    }

    commands[args.command](args)
