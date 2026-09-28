---
name: requirement-analysis
description: Turn teacher-service work into testable requirements under the authoritative Turkish CPT labeling contract.
---

# Requirement Analysis — LinguAI Teacher

Before material code changes, read `AGENTS.md`, the complete quality spec, exact system/user prompts, response schema, relevant features, architecture notes and current source.

Record the actor and user outcome, request/response fields, trust boundary, service-owned versus VPS-owned data, success/rejection/boundary cases, security/privacy, operational bounds, non-goals, tests and acceptance evidence. Identify whether a decision changes class semantics, thresholds, prompt behavior, dataset spend, security or provenance. Keep those decisions OPEN until the user/project contract supplies an answer; safe implementation details may be marked SAFE_DEFAULT with rationale.

Do not infer the teacher's class meaning, score thresholds, model, quantization, serving engine, license, token cap, concurrency, host network, calibration set or budget. A reported 48 GB VRAM is not sufficient evidence. Use the prompt/schema and caller in `serda-dev/linguai-dataset-quality` as authority and preserve immutable source commit/hash provenance.

Update the feature/spec and open-question register before implementation. Teacher response contains observations only; keep policy routing/provenance in the VPS envelope. No GPU or real inference spend is authorized by writing a requirement.
