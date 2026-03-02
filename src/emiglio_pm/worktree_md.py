"""Generate WORKTREE.md from manifest + Jinja2 template."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from emiglio_pm.manifest import Manifest, Workstream, find_repo_root


def _template_dir() -> Path:
    return Path(__file__).parent / "templates"


def _load_instructions(ws: Workstream, repo_root: Path) -> str:
    """Load the detailed instructions markdown file for a workstream."""
    if not ws.instructions:
        return ""
    path = repo_root / ws.instructions
    if not path.exists():
        return f"(instructions file not found: {ws.instructions})"
    return path.read_text().strip()


def render_worktree_md(manifest: Manifest, name: str, repo_root: Path | None = None) -> str:
    """Render WORKTREE.md content for a workstream."""
    if repo_root is None:
        repo_root = find_repo_root()

    ws = manifest.workstreams[name]
    instructions = _load_instructions(ws, repo_root)

    env = Environment(
        loader=FileSystemLoader(str(_template_dir())),
        keep_trailing_newline=True,
    )
    template = env.get_template("WORKTREE.md.j2")

    return template.render(
        ws=ws,
        project=manifest.project,
        instructions=instructions,
    )


def sync_worktree_md(manifest: Manifest, name: str, repo_root: Path | None = None) -> Path:
    """Generate WORKTREE.md into a worktree directory."""
    if repo_root is None:
        repo_root = find_repo_root()

    from emiglio_pm.git_ops import worktree_path

    wt = worktree_path(manifest, name, repo_root)
    if not wt.exists():
        raise FileNotFoundError(f"Worktree not found: {wt}")

    content = render_worktree_md(manifest, name, repo_root)
    out = wt / "WORKTREE.md"
    out.write_text(content)
    return out
