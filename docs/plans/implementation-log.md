# Implementation log

Append a dated entry for material changes. Record the requirement and architecture references, changed behavior, model/runtime revision if used, test commands/results, skipped boundaries, audit findings, and deployment status. Never include API keys, notebook tokens, document samples, full teacher prompts, or labels.

## Entries

### 2026-09-28 — Repository preparation

- Added agent workflow, project-specific skill roles, authoritative contracts and acceptance features.
- No model-serving code, model download, GPU setup, inference request, calibration call, or deployment was performed.
- The source prompt, user payload template, JSON schema and quality specification match byte-for-byte with `linguai-dataset-quality` main commit `39c17b4b441b31112a1db6159380a9a034a1bef2`; fingerprints are recorded in `docs/requirements/source-contracts.md`.
- GPU, model, serving engine, and actual latency remain unmeasured/open.

## 2026-09-28 — source-built Qwen service

Sequential roles completed: Requirement Analyst (`runtime-v1.md`, token feature,
decision register), Architect (ADR 0002), Senior Developer (WSGI gateway,
llama.cpp adapter, supervisor, CUDA Docker/Compose, publish/smoke tools), Ponytail
(one backend/one gateway, no extra queue/store), Meaningful Tests, Engineering
Audit (separate self-review pass; no claim of independent reviewer).

Current VPS caller/contracts/settings were read from main. Caller messages are
preserved verbatim; timeout remains 20 s. No changes made to the VPS repo.

Executed: 22 `unittest` tests on Python 3.12.14 with JSON Schema 4.26.0 and its
installed dependencies; loopback WSGI success, backend HTTP deadline, child process
termination, valid/invalid contract, exact-token boundary, auth and overload.
`compileall` and `bash -n scripts/publish.sh` pass. No real teacher request made.

Not executed: Docker test stage/full CUDA build, Gunicorn runtime startup, real
llama.cpp model/template/kernel test, published registry pull, Vast startup,
actual TLS/SSH/Coolify reachability, GPU memory/p95, A–H semantic calibration.
Docker/CUDA/GPU are absent and direct package downloads are unavailable in this
authoring environment. Official sources were read through GitHub/HF/web tools.
Existing local JSON Schema dependencies enabled CPU validation without downloads.

Publishing script first runs the Docker CPU test target, then builds/pushes an
image tagged with the clean git commit and reports its digest. No automatic
GitHub Actions run or remote deployment is configured by this change.
