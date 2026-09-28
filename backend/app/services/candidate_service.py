"""Candidate generation: copy the champion into an isolated workspace and apply
the improvement agent's proposed, whitelisted modifications.

The LLM never writes to production. It writes to experiments/candidates/<id>/.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from .. import security
from ..audit import audit
from ..config import get_settings
from ..models import Candidate, Champion, Experiment
from . import git_service


def _champion_sut_dir(champion: Champion) -> Path:
    return Path(champion.sut_path)


def apply_modifications(candidate_ws: Path, modifications: list[dict]) -> list[str]:
    """Apply validated modifications; return the list of files changed."""
    changed: set[str] = set()
    for mod in modifications:
        mtype = mod.get("type")
        if mtype == "config_update":
            updates = security.validate_config_update(mod.get("updates", {}))
            cfg_path = candidate_ws / "sut" / "pipeline.yaml"
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            cfg.update(updates)
            cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            changed.add("sut/pipeline.yaml")
        elif mtype in ("file_write", "prompt_update"):
            rel = mod.get("path") if mtype == "file_write" else "sut/pipeline.yaml"
            content = mod.get("content", "")
            if mtype == "prompt_update":
                updates = security.validate_config_update({"system_prompt": content})
                cfg_path = candidate_ws / "sut" / "pipeline.yaml"
                cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
                cfg.update(updates)
                cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            else:
                security.scan_code(content, rel)
                target = security.resolve_within(candidate_ws, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            changed.add(rel)
        else:
            raise security.SecurityViolation(f"unknown modification type: {mtype!r}")
    return sorted(changed)


def create_candidate(db: Session, experiment: Experiment, hypothesis: dict,
                     champion: Champion) -> Candidate:
    settings = get_settings()
    candidate = Candidate(
        experiment_id=experiment.id,
        parent_version=champion.version,
        description=hypothesis.get("proposed_change", ""),
        status="GENERATING",
    )
    db.add(candidate)
    db.flush()

    ws = settings.candidates_dir / candidate.id
    ws.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_champion_sut_dir(champion), ws / "sut",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    files_changed = apply_modifications(ws, hypothesis.get("modifications", []))

    (ws / "CHANGELOG.md").write_text(
        f"# Candidate {candidate.id}\n\n"
        f"- Parent: {champion.version}\n"
        f"- Hypothesis: {hypothesis.get('hypothesis', '')}\n"
        f"- Change: {hypothesis.get('proposed_change', '')}\n"
        f"- Expected metric: {hypothesis.get('expected_metric', '')} "
        f"+{hypothesis.get('expected_improvement', 0)}\n",
        encoding="utf-8",
    )
    (ws / "PATCH_SUMMARY.md").write_text(
        "# Patch summary\n\n"
        + "\n".join(f"- `{f}`" for f in files_changed)
        + f"\n\nRisk: {hypothesis.get('risk', 'unknown')}\n"
        + "\nRollback: delete this candidate directory; the champion is untouched.\n",
        encoding="utf-8",
    )

    candidate.path = str(ws)
    candidate.files_changed = files_changed
    candidate.status = "CREATED"
    db.commit()

    commit = git_service.commit_paths([ws], f"candidate {candidate.id}: "
                                      f"{hypothesis.get('strategy', 'experiment')}")
    if commit:
        candidate.git_branch = commit[:12]
        db.commit()

    audit(db, "CANDIDATE_CREATED", candidate=candidate.id, files=files_changed)
    return candidate
