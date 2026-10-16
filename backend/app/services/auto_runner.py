"""Run improvement cycles back to back.

Passing candidates are promoted automatically when REQUIRE_HUMAN_APPROVAL is
false; otherwise the run pauses so a human can approve in the UI. State is kept
in memory, so a backend restart ends any auto run.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone

from ..audit import audit
from ..config import get_settings
from ..database import SessionLocal
from ..graph.improvement_graph import run_experiment_sync
from ..models import Candidate, Experiment
from . import promotion_service

_lock = threading.Lock()
_state: dict = {
    "running": False, "cycles_requested": 0, "cycles_completed": 0, "promoted": [],
    "current_experiment": None, "stop_reason": None, "stop_requested": False,
    "started_at": None, "finished_at": None,
}


def status() -> dict:
    return {**_state, "promoted": list(_state["promoted"])}


def start(cycles: int) -> dict:
    if not _lock.acquire(blocking=False):
        raise RuntimeError("an auto run is already in progress")
    _state.update(running=True, cycles_requested=cycles, cycles_completed=0, promoted=[],
                  current_experiment=None, stop_reason=None, stop_requested=False,
                  started_at=datetime.now(timezone.utc).isoformat(), finished_at=None)
    threading.Thread(target=_run_and_release, args=(cycles,), daemon=True).start()
    return status()


def request_stop() -> dict:
    if _state["running"]:
        _state["stop_requested"] = True
    return status()


def _run_and_release(cycles: int) -> None:
    try:
        run_cycles(cycles)
    finally:
        _lock.release()


def run_cycles(cycles: int) -> str:
    reason = f"completed {cycles} cycles"
    try:
        for i in range(cycles):
            if _state["stop_requested"]:
                reason = "stopped by user"
                break
            with SessionLocal() as db:
                exp = Experiment(objective="Improve the benchmark score (auto run)")
                db.add(exp)
                db.commit()
                exp_id = exp.id
            _state["current_experiment"] = exp_id
            run_experiment_sync(exp_id)
            _state["cycles_completed"] = i + 1

            with SessionLocal() as db:
                exp = db.get(Experiment, exp_id)
                if exp.status == "FAILED":
                    reason = ("no new ideas" if (exp.error or "").startswith("No new ideas")
                              else f"experiment {exp_id} failed: {(exp.error or '')[:200]}")
                    break
                if exp.status == "AWAITING_APPROVAL":
                    if get_settings().require_human_approval:
                        reason = f"experiment {exp_id} passed and is awaiting human approval"
                        break
                    cand = db.query(Candidate).filter_by(experiment_id=exp_id).one()
                    champion = promotion_service.promote(db, cand, approved_by="auto-run",
                                                         reason="passed gate during auto run")
                    _state["promoted"].append(champion.version)
    except Exception as exc:  # noqa: BLE001 — report why the run stopped
        reason = f"error: {exc}"[:300]
    finally:
        _state.update(running=False, current_experiment=None, stop_reason=reason,
                      finished_at=datetime.now(timezone.utc).isoformat())
        with SessionLocal() as db:
            audit(db, "AUTO_RUN_FINISHED", cycles=_state["cycles_completed"],
                  promoted=_state["promoted"], reason=reason)
    return reason
