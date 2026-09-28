# GPU runtime v1 — 2026-09-28

Latest user authorization: implement a repository-built Docker image for Vast.ai,
connect it to the existing VPS, research Qwen30A3B and prefer Ollama or a source
build over vLLM. Direct main push is authorized. Renting/deploying a GPU is not
performed by this change.

## Requirements and acceptance

| ID | Behavior | Evidence |
| --- | --- | --- |
| R1 | Serve the existing two-message, temperature-zero caller at `/v1/chat/completions`; exact versioned prompt and user template | HTTP contract tests |
| R2 | Bearer authentication before body/backend work; bounded body and response; redacted errors | Auth/size/error tests |
| R3 | Render the model template once, tokenize with the actual loaded tokenizer, reserve output + safety, reject overflow; no truncation or context shifting | Exact-boundary and forwarded-token tests |
| R4 | Independent Draft 2020-12 validation and exact document ID; reject partial output and wrong IDs without repair/retry | Invalid-output tests |
| R5 | One active inference; no durable queue; 18-second backend deadline under the caller's 20 seconds | Overload/deadline tests, actual VPS latency pending |
| R6 | Source-pinned CUDA llama.cpp image, immutable official Qwen GGUF revision and checksum, persistent model cache | Manifest/launcher checks; CUDA build and GPU load pending |
| R7 | Non-generating liveness/readiness and model/profile metadata; child failure stops container; graceful termination | Probe/supervisor tests |
| R8 | Vast Entrypoint instructions, explicit SSH/Jupyter startup override, actual mapped port, TLS or SSH connection, local image publish tool | Runbook and smoke client |
| R9 | Keep authoritative labels, provenance and routing in VPS; no dataset/database credentials on GPU | Source audit |

`Qwen30A3B` is resolved to the official original `Qwen/Qwen3-30B-A3B-GGUF`,
not Qwen3.5 and not the distinct Instruct-2507 model. The profile makes this
explicit. Q8_0 is a provisional higher-precision quantized starting point;
48 GB is a target, not measured fitness. No silent fallback to a smaller model.

SAFE_DEFAULT: 8192 context tokens, 1024 maximum output tokens, 32 safety tokens,
one generation, 8000 gateway port, 8081 loopback backend, 1 MiB request bytes,
18 s backend deadline. These are operational limits, not quality thresholds.
The existing caller remains unchanged (20 s timeout / 60 s lease / 30 s
heartbeat). Longer deadlines require a separate caller/lease review.

OPEN: actual GPU/driver/free memory, Docker build on target architecture,
VRAM peak, latency, secure endpoint/certificate or SSH route, and human-approved
A–H semantic calibration. No promise of zero runtime errors: invalid context,
load failure and overload must fail explicitly rather than corrupt labels.
