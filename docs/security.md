# Security model

The POC is deliberately **not** an uncontrolled autonomous system.

## What the agent may do

- Propose hypotheses as structured JSON.
- Modify whitelisted files inside its own candidate workspace:
  `sut/pipeline.yaml` (whitelisted keys only), `sut/retrieval.py`,
  `sut/rerank.py`, `sut/rewrite.py`.
- Read experiment history and strategy statistics through MCP tools.

## What the agent may never do

- Modify the benchmark, expected answers, or evaluator (mounted read-only in
  the sandbox; hashed before/after every run).
- Modify promotion rules, security controls, the audit log, or the human
  approval mechanism.
- Access production, credentials, `.env`, or the host filesystem outside its
  workspace.
- Promote itself. Promotion requires explicit human approval
  (`REQUIRE_HUMAN_APPROVAL=true`).

## Mechanisms

- **Path validation**: no `..`, no absolute paths, no symlinks escaping the
  candidate workspace, whitelist enforcement (`backend/app/security.py`).
- **Static screening**: candidate code is scanned for subprocess, network,
  eval/exec, and other dangerous patterns before execution.
- **Sandbox**: Docker with `--cpus`, `--memory`, read-only mounts, timeout.
  Local fallback is flagged `isolated=false` in results and audit.
- **Promotion gate**: hard constraints (latency ceiling, zero failures, no
  quality regression) + minimum composite improvement + human approval.
- **Audit**: every experiment, hypothesis, candidate, sandbox run, benchmark,
  approval, and promotion is written to `audit_log`.

## Not in the POC (intentionally disabled)

Autonomous weight modification, model downloading, internet access from the
sandbox, production deployment, self-replication, credential access.
