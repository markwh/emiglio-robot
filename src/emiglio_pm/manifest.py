"""Load and validate workstreams.yml manifest."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ProjectConfig:
    base_branch: str
    stable_branch: str
    worktree_root: str
    develop_color: str = ""


@dataclass
class Workstream:
    name: str
    branch: str
    role: str
    summary: str
    scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    instructions: str = ""
    color: str = ""


@dataclass
class Manifest:
    project: ProjectConfig
    workstreams: dict[str, Workstream]


def find_repo_root(start: Path | None = None) -> Path:
    """Find the main git repo root, handling worktree .git files."""
    start = start or Path.cwd()
    current = start.resolve()

    while current != current.parent:
        git_path = current / ".git"
        if git_path.is_dir():
            return current
        if git_path.is_file():
            # Inside a worktree — .git is a file with "gitdir: <path>"
            text = git_path.read_text().strip()
            if text.startswith("gitdir:"):
                gitdir = Path(text.split(":", 1)[1].strip())
                if not gitdir.is_absolute():
                    gitdir = (current / gitdir).resolve()
                # gitdir points to .git/worktrees/<name> in the main repo
                # Walk up to find the main .git dir
                main_git = gitdir
                while main_git.name != ".git" and main_git != main_git.parent:
                    main_git = main_git.parent
                return main_git.parent
        current = current.parent

    raise FileNotFoundError("Not inside a git repository")


def load_manifest(repo_root: Path | None = None) -> Manifest:
    """Load workstreams.yml from the repo root."""
    if repo_root is None:
        repo_root = find_repo_root()

    manifest_path = repo_root / "workstreams.yml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No workstreams.yml found at {manifest_path}")

    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    proj = data["project"]
    project = ProjectConfig(
        base_branch=proj["base_branch"],
        stable_branch=proj["stable_branch"],
        worktree_root=proj["worktree_root"],
        develop_color=proj.get("develop_color", ""),
    )

    workstreams: dict[str, Workstream] = {}
    for name, ws in data["workstreams"].items():
        workstreams[name] = Workstream(
            name=name,
            branch=ws["branch"],
            role=ws["role"],
            summary=ws["summary"],
            scope=ws.get("scope", []),
            out_of_scope=ws.get("out_of_scope", []),
            instructions=ws.get("instructions", ""),
            color=ws.get("color", ""),
        )

    return Manifest(project=project, workstreams=workstreams)
