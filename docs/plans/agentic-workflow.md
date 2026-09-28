# Agentic implementation sequence

This is a work order, not authorization to select an unapproved teacher or start large inference.

## Phase 0 — Requirements and inventory

- Requirement Analyst verifies the exact system prompt and schema hashes against `serda-dev/linguai-dataset-quality` at a named commit.
- Inventory GPU/driver/runtime/storage/network over the operator-provided SSH session without printing credentials or exposing Jupyter tokens.
- Resolve Q-01 through Q-09 as needed. Keep unresolved consequential choices marked `OPEN`.
- Produce an acceptance checklist and explicitly approved model/profile/calibration scope.

## Phase 1 — Architecture

- Architect proposes one serving engine/model profile based on measured host compatibility and API constraints.
- Record pinned model ID/revision, image/runtime versions, memory budget, context cap, output cap, concurrency, timeout, auth, encrypted route, logs, health checks and recovery.
- Confirm model can enforce or produce strict JSON; regardless, server validates ID and schema itself.
- Do not download weights or start a cost-bearing model process before the host and profile are agreed.

## Phase 2 — Mock contract implementation

- Implement API/auth/request validation against a deterministic mock model first.
- Test exact prompt and user-payload forwarding, model allowlist, output envelope/string, valid JSON/schema/ID, failure handling, redaction, limits and non-labeling health checks.
- Run tests locally/in Docker if available. Never use GitHub Actions as a required gate.

## Phase 3 — GPU deployment

- Provision only after the user supplies the access link and intended rental window. Pin setup steps and avoid printing notebook/Jupyter access tokens.
- Confirm actual VRAM under inference, model load, context, concurrency, p50/p95 latency, restart behavior and VPS reachability over the approved secure route.
- Reject the profile if it exceeds the caller deadline until the dependent VPS timeout/lease/heartbeat behavior is reviewed and separately tested.

## Phase 4 — Tiny calibration and handoff

- Use only the exact small set and model call count approved by the user. Calibrate acceptance exemplars A–H against the authoritative rubric; do not tune thresholds or rewrite the prompt silently.
- Record disagreements, failed JSON rate, memory peak, latency and pinned provenance. Stop when the approved count is reached.
- Handoff endpoint, auth setup out of band, exact model/revision/profile, deployment instructions and observed limitations. Do not trigger any 40k or other broad labeling run.

## Phase 5 — Independent audit and version control

- Engineering Auditor reviews the implementation against requirements and features; reports evidence with findings.
- Address accepted findings, run meaningful tests, update implementation/audit logs.
- Push focused, verified commits to the requested branch. No PR is needed only when the user explicitly requests direct push; no production deployment follows automatically.
