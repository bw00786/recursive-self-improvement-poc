# Architecture

## Control plane vs system under test

```
┌──────────────────────── CONTROL PLANE (never modifiable by the agent) ─┐
│ benchmark/  evaluator  promotion rules  security  audit  human gate    │
└─────────────────────────────────────────────────────────────────────────┘
┌────────────────────── IMPROVEMENT AGENT (Llama 3.1) ────────────────────┐
│ analyze -> hypothesize -> research -> generate candidate                │
└─────────────────────────────────────────────────────────────────────────┘
┌────────────────────── SYSTEM UNDER TEST (sut/) ─────────────────────────┐
│ question -> [rewrite] -> [retrieve keyword|vector|hybrid] -> [rerank]   │
│          -> LLM -> cited answer                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## The loop

1. `load_champion` — fetch (or bootstrap + baseline) the active champion.
2. `analyze_performance` — find the weakest metrics.
3. `generate_hypothesis` — one measurable, reversible modification (JSON,
   schema-validated; malformed LLM output is rejected and the deterministic
   playbook is used).
4. `research_solution` — local knowledge attached to the hypothesis.
5. `generate_candidate` — copy champion into `experiments/candidates/<id>/`,
   apply whitelisted modifications, write CHANGELOG/PATCH_SUMMARY, git commit.
6. `validate_candidate` — whitelist + static code screening.
7. `run_sandbox` — Docker (CPU/memory limits, read-only mounts, timeout);
   benchmark hashed before/after to prove immutability.
8. `evaluate_candidate` — per-metric rows persisted.
9. `compare_with_champion` — hard constraints + composite score delta.
   Pass → `AWAITING_APPROVAL` (human gate). Fail → recorded as strategy data.

## The recursive layer

Every experiment updates `strategies` (success rate, average improvement).
The improvement agent receives those statistics when choosing its next
hypothesis, so the system learns **which kinds of improvements work** — it
improves its own improvement strategy.

## Data model

`champions` (one active), `experiments`, `candidates`, `evaluations`
(per-metric), `strategies` (learned stats), `audit_log` (every event).
