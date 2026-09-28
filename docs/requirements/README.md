# Requirements index

## Binding contracts

- [`TURKISH_CPT_DATA_QUALITY_SPEC_v1.md`](TURKISH_CPT_DATA_QUALITY_SPEC_v1.md) — authoritative semantics and rubric.
- [`../../prompts/turkish_cpt_quality_teacher_v2.txt`](../../prompts/turkish_cpt_quality_teacher_v2.txt) — exact system prompt; do not edit without a new prompt version.
- [`../../prompts/teacher_user_v1.txt`](../../prompts/teacher_user_v1.txt) — exact document payload template.
- [`../../schemas/teacher_label_v1.schema.json`](../../schemas/teacher_label_v1.schema.json) — exact teacher reply schema.
- [`../../features/`](../../features/) — acceptance behavior.

## Service outcome

Run a selected, version-pinned teacher model on a supplied GPU and expose a bounded, authenticated OpenAI-compatible inference API to the existing LinguAI VPS control plane. The client uses `POST {TEACHER_BASE_URL}/chat/completions`, with `TEACHER_BASE_URL` ending in `/v1`, model identifier, `temperature: 0`, the exact system prompt, and a user payload with document ID and sketch. Success returns a JSON object in `choices[0].message.content` that independently validates against the committed response schema and has the same ID.

The service owns model inference only. The VPS owns source documents, sampling, user approvals, queue, durable attempts and labels, policy routing, provenance and exports. No source-dataset name is sent to the teacher by default.

## Non-goals

- Corpus discovery/download, document persistence, data cleaning/repair, policy routing, training a student, annotation UI, or writing to the VPS database.
- Treating the “48 GB” report as proof of fit or accepting a model/profile without actual host measurements.
- Full-scale teacher labeling or spend during setup. Live semantic calibration needs an explicitly approved tiny set.

## Acceptance and decisions

Requirements are in `features/`. Unresolved items are tracked in [`open-questions.md`](open-questions.md). A missing decision that changes class meaning, thresholds, teacher behavior, security exposure, spend, or provenance is a blocker; do not silently supply a domain answer. Safe, reversible implementation details can be recorded as safe defaults with rationale.

Implementation requirements: [runtime-v1.md](runtime-v1.md). Candidate choices are recorded in ADR 0002 under the latest implementation authorization.
