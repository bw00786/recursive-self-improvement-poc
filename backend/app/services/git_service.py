"""Best-effort git integration. The loop must work even without a git repo."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import get_settings


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=get_settings().repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )


def ensure_repo() -> bool:
    if (get_settings().repo_root / ".git").exists():
        return True
    return _git("init").returncode == 0


def current_commit() -> str | None:
    r = _git("rev-parse", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else None


def commit_paths(paths: list[Path], message: str) -> str | None:
    """Commit the given paths; return the commit hash or None if git is unusable."""
    if not ensure_repo():
        return None
    rels = [str(p.relative_to(get_settings().repo_root)) for p in paths]
    if _git("add", *rels).returncode != 0:
        return None
    # Nothing to commit is fine.
    _git("-c", "user.email=rail@local", "-c", "user.name=rail", "commit",
         "-m", message, "--allow-empty")
    return current_commit()
