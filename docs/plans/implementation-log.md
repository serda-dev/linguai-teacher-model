# Implementation log

Append a dated entry for material changes. Record the requirement and architecture references, changed behavior, model/runtime revision if used, test commands/results, skipped boundaries, audit findings, and deployment status. Never include API keys, notebook tokens, document samples, full teacher prompts, or labels.

## Entries

### 2026-10-02 — Vast instance 53864048 connected to Coolify

- Confirmed the rented RTX A6000 instance pulls the public release image. The
  official Qwen Q8 GGUF passed its pinned SHA-256 check and loaded on GPU at
  about 31 GiB VRAM. Authenticated `/ready` reported the expected model,
  revision, profile and llama.cpp commit.
- Vast did not inject the updated instance environment into its already-running
  SSH container. Stored the API key only in a mode-600 file under `/workspace`
  and added a mode-700 onstart launcher there; `/root/onstart.sh` now relaunches
  it after an instance restart. No key was recorded in this repository.
- Started a restartable SSH forwarding sidecar on the Coolify network, forwarding
  only to the GPU container's loopback port. The public mapped port refused a
  direct connection. Coolify's `linguai-dataset-quality` API, worker and Postgres
  started after repairing a stale Postgres role password and URL configuration.
- VPS `/ready` and GPU `/ready` passed. A single synthetic, non-persisted request
  from the VPS API container returned a schema-valid label with the expected ID
  in 1.47 seconds. No source dataset was enrolled; run, document, job and label
  counts remained zero. Semantic calibration and real-data latency remain open.

### 2026-10-02 — Vast SSH template preparation

- Added a private Vast SSH template creation script and documented its tunnel-only
  API topology. The image entrypoint is replaced in SSH mode, so onstart invokes
  `teacher_service.launch`; port 8000 binds to container loopback.
- `docker build --target test -t linguai-teacher:test .` passed all 22 CPU/HTTP tests.
  `bash -n scripts/create_vast_template.sh` and `git diff --check` passed.
- The full CUDA build was started, then canceled on the production VPS while
  CUDA compilation was still in progress. No full image or registry artifact was
  produced, and no GPU model load or inference was run.
- Vast CLI is installed, but account actions report that a 2FA session is
  required. The image is not available locally or confirmed pullable from GHCR.
  No template or paid instance was created. Publish and verify the image, then
  create and inspect the template before renting a machine.

### 2026-10-02 — Vast account template registered

- After the Vast API key was updated, created private SSH template ID `748997`
  (`8e1fb5fa3eb15433f66ab50492e1eec6`) and independently read it back.
  It points to the Teacher image tag for the then-current source revision,
  recommends 80 GB disk, sets loopback binding, and runs the launcher in onstart.
- Added a dedicated SSH public key to the Vast account for the eventual VPS
  tunnel. The private key stays on this VPS; no key material was put in Git or
  in the template.
- The template registration does not rent an instance or verify the image pull.
  The image reference must be updated to the digest/tag actually published and
  verified before the user chooses an offer.

### 2026-10-02 — Teacher image published

- Full source-built CUDA image completed on this VPS with llama.cpp commit
  `7fe450e19305b828c199d602c23a8337aaa1f03b`, CUDA 12.8.1 and SM
  80/86/89/90 build targets. Published `ghcr.io/serda-dev/linguai-teacher-model:e347027`
  from repository commit `e34702721623778dfd5e13abe2eed187051c5148`.
- GHCR reported manifest-list digest
  `sha256:02f84fbe4d5f23ad8d4fd390140a59431e006fe282fa82d581040aabba1e291e`.
  A local container check found the pinned profile, schema and `llama-server`
  binary; it did not load the model or use a GPU.
- Updated Vast template ID `748997` to the release tag and read back its SSH
  mode, loopback-only environment, onstart launcher, 80 GB disk and private
  template visibility. The update CLI replaces unspecified settings, so the
  create/update script now sends all settings in either mode.
- Anonymous GHCR manifest access was denied while the package was private.
  The user selected public package visibility; GitHub requires a package
  settings action before anonymous pulls can be verified. No GPU instance was
  rented and no teacher labels were generated.
- After the user made the GHCR package public, an empty-credential Docker
  configuration fetched its manifest and pulled the image successfully.
  The pull reported the same manifest-list digest as the publish step. Vast
  template ID `748997` was read back again with the published tag, SSH mode,
  loopback binding, onstart command and 80 GB disk intact.

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
