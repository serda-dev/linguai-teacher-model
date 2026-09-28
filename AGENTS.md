# Agent operating contract

This repository builds a replaceable GPU inference service that labels one supplied Turkish CPT document at a time. Follow the order below for material work. Do not infer model, hardware, serving-engine, network, calibration, or cost decisions from an example name or a VRAM figure.

## Required workflow

1. **Requirement Analyst** — read the authoritative documents and current code; identify user outcome, request/response contract, security boundary, acceptance criteria, non-goals, and open decisions. Record ambiguity instead of inventing domain behavior.
2. **Solution Architect** — design the smallest implementation against the approved contract. Document the API boundary, model lifecycle, GPU allocation, bounded concurrency/context, startup/readiness, failure and shutdown behavior, security and observability. Mark decisions that require actual host/model measurements.
3. **Senior Developer** — implement only approved requirements. Keep documents, labeling jobs, accepted labels, provenance and durable state on the VPS. This service accepts an inference request and returns a validated response; it does not fetch datasets or write to the VPS database.
4. **Ponytail review** — challenge unnecessary layers, packages, services and complexity; keep the smallest maintainable serving path.
5. **Meaningful Tests** — add falsifiable unit, HTTP-contract and deployment tests. Use mocks for deterministic tests; use the actual selected model only with an explicitly approved tiny calibration set. Never use a full corpus as a test.
6. **Engineering Audit** — independently inspect the completed change and report confirmed defects, evidence, impact and smallest recommendation. Audit does not silently change code.
7. **Version Control** — inspect status/diff, run appropriate tests, keep commits focused, and report exactly what was pushed. Do not merge or deploy without explicit user authorization.

For a one-line change, use judgment and do not create ceremonial documents. For a material behavior change, complete and update the relevant requirement, architecture, feature, implementation and audit artifacts before calling the work done.

## Authority and invariants

- `docs/requirements/TURKISH_CPT_DATA_QUALITY_SPEC_v1.md`, `prompts/turkish_cpt_quality_teacher_v2.txt`, `prompts/teacher_user_v1.txt`, and `schemas/teacher_label_v1.schema.json` are authoritative. The teacher system prompt must be copied and sent verbatim. Do not silently edit it, truncate the original document, or add unapproved output fields.
- The API reply must be OpenAI-compatible and its `choices[0].message.content` must contain only a schema-valid JSON string for the requested document ID. Independently validate model output before reporting success. Never repair a wrong ID by replacing it.
- Teacher output is observation only. Never emit KEEP/DROP, routing, provenance or repair instructions in the teacher label.
- Quality dimensions are independent. High information with low cleanliness is valid. Code, mathematics, tables, dialogue and structured data are not inherently low quality.
- The GPU host is disposable. It receives no source-corpus credentials and does not own durable jobs, documents, labels or exports. Do not log raw documents, complete prompts, credentials or generated labels.
- 48 GB VRAM does not prove a model fits. Measure actual card, free memory, weights, KV cache, runtime overhead, context, concurrency and latency on the supplied host.
- The current caller timeout is 20 seconds; the control-plane worker lease is 60 seconds and heartbeat freshness is 30 seconds. Any proposed latency/timeout/concurrency change must assess these together and update the caller in its own reviewed change.
- No dataset run, bulk labeling, spend, production endpoint or public port is authorized by this repository setup. Health/readiness probes must never trigger inference or create labels.
- Keep secrets out of Git, notebook output, logs, test fixtures, screenshots and command output. Use `.env.example` only for names and placeholders.

## Before declaring complete

State the files changed, behavior, tests actually run, tests skipped and why, selected hardware/model/profile if known, and unresolved decisions. Do not claim GPU fit, live endpoint reachability, model quality or production readiness without having measured it on the actual host.
