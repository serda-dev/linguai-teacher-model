# Test plan

The test harness and chosen server framework are future implementation decisions. Do not add test dependencies before architecture selects the runtime.

## Deterministic tests (no GPU, no real documents)

- Schema meta-validation and positive/negative label examples; unknown/additional keys, ranges, null-only natural-language exception, unique/allowed noise flags and ID mismatch.
- API request shape and exact system/user message forwarding, model allowlist and temperature behavior.
- OpenAI-compatible completion envelope with content as a JSON string.
- Reject prose, fenced JSON, malformed JSON, multiple objects, extra fields, invalid score/type/noise and mismatched IDs; bound retry count and response size.
- Auth missing/invalid, oversized request, unsupported model, overload and backend errors; ensure document/prompt/credential/label text never leaks into errors/log fields.
- Health versus readiness, startup/load/OOM, no-label probes, shutdown and replacement behavior using a fake backend.
- No database, corpus, queue, storage-write or source-credential integration exists on the GPU service.

## Container and deployment checks

- Build image from pinned dependencies and a documented base; prove the process binds to the configured interface and stops cleanly.
- Health probes are non-labeling. Secrets are injected at runtime; the image and logs contain no model credentials or prompt/document fixtures.
- Exercise one valid request and representative bounded failure cases from a test client over the intended private route.

## Actual-GPU checks (only after explicit profile approval)

- Record actual GPU/card count, driver, runtime, initial free memory and memory peak during model load and representative inference.
- Verify pinned model revision, context length, full-prompt preservation, output length, schema-valid rate, exact ID preservation and controlled OOM behavior.
- Measure end-to-end p50/p95 from the VPS; compare with its 20-second request timeout, 60-second job lease and 30-second heartbeat freshness.
- Test only the explicitly approved tiny calibration set; stop at its exact count. No full corpus and no speculative load sweep that incurs unapproved compute charges.

## Reporting

Separate tests run from skipped/unavailable tests. A mock or CPU-only test does not prove GPU fit, real-network reachability, teacher quality, license suitability or production safety.
