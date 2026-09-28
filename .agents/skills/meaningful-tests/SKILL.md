---
name: meaningful-tests
description: Test the LinguAI teacher request, schema, security and bounded GPU runtime contracts with falsifiable cases.
---

# Meaningful Tests — LinguAI Teacher

Read `AGENTS.md`, `docs/tests/test-plan.md`, the exact prompt/schema, features, architecture and current server/client tests first. Use CPU mocks for deterministic tests and isolate actual GPU/inference checks from routine CI/local tests.

For each behavior, add a test that fails for a plausible wrong implementation: valid request success; missing/invalid auth; boundary-sized and oversized request; unsupported model; malformed JSON, schema violations, extra fields, wrong ID, prose/fences; backend timeout/OOM; overload; no raw content in errors/logging; probes do not invoke inference; and no VPS database/job writes. Verify retries are bounded and do not silently rewrite IDs or labels.

Run the documented local and Docker gates. Report PostgreSQL/network/GPU/model/latency/license boundaries that mocks cannot verify. Actual model tests must use the exact approved tiny calibration set and stop at its approved count. Never put real documents, keys or Jupyter tokens in tests or logs.
