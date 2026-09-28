# ADR 0002 — source-built Qwen teacher

Date: 2026-09-28. Status: implemented candidate, GPU acceptance pending.
Supersedes the unselected implementation choices in ADR 0001 and initial boundary.

## Decision

One container runs a source-built llama.cpp server on 127.0.0.1:8081 and a small
Python WSGI gateway under Gunicorn (one process, four HTTP threads) on port 8000.
A process supervisor downloads/verifies the model, starts both children, and
terminates both if either fails. No database, durable queue, automatic inference
retry, model registry, UI or routing policy.

Use official Qwen3-30B-A3B Q8_0 GGUF; see `profiles/qwen3-30b-a3b-q8.json` for
revision and SHA256. Official model license is Apache-2.0. llama.cpp v0.5.0 is
built from commit `7fe450e19305b828c199d602c23a8337aaa1f03b` (MIT). Build CUDA
12.8.1 for Ampere/Ada/Hopper, Python 3.12 on Ubuntu 24.04. Host driver/GPU support
must still be checked; source and package pins are committed, while OS base tags
are mutable and the *built image digest* must be recorded for deployment.

## Why source build rather than Ollama

Both support Qwen. llama.cpp provides `/apply-template` and `/tokenize` without
inference. The gateway renders once, counts actual special tokens, then sends
those exact token IDs to `/completion`. It checks `input + output + 32 <= n_ctx`.
The backend runs with explicit context, `--fit off`, one slot, all GPU layers
and `--no-context-shift`. Generation is schema-constrained, temperature zero,
thinking disabled through template configuration, with independent validation.
No prompt suffix is added and no token estimate or silent clipping is used.
Ollama's documented chat API has no equivalent exact pre-tokenization flow;
floating `qwen3:30b` aliases also obscure original versus Instruct-2507 identity.

## Lifecycle, failure and security

Download uses an immutable HTTPS URL, resumable curl, size/hash verification and
atomic rename. Only the selected file is downloaded. Cached weights are verified
on each start; corruption fails closed. Initial download can take many minutes.
Gateway starts after model load; before that readiness is unavailable. Health
uses process status, readiness checks backend health/context/model metadata and
never produces a completion. One application semaphore prevents generation
queueing; `/slots` rejects requests while cancellation is still draining.
An 18 s monotonic backend deadline includes preparation and generation; socket
closure cancels the backend request. No generation retry. Client disconnect may
leave at most this bounded work running. Backend failure makes readiness fail;
child exit stops the whole container. Termination is forwarded with bounded kill.

The backend is never published. Auth is required for models/readiness/completions.
Gunicorn access logs are disabled; gateway errors are constant codes; backend
stdout/stderr are discarded because upstream diagnostics can include content.
Lifecycle logs contain phase names and exit codes only. TLS is supported directly
with mounted certificate/key, or use an authenticated SSH tunnel and bind the
API privately. Do not expose raw plaintext document traffic over the Internet.

The API retains no durable request/label storage. Backend KV memory is ephemeral;
prompt caching is disabled per request, but GPU/process memory is not a forensic
secure-erase guarantee. Replacing the GPU does not mutate accepted VPS labels.

## Official sources checked

- https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF/tree/e4d4bafdfb96a411a163846265362aceb0b9c63a
- https://github.com/ggml-org/llama.cpp/tree/7fe450e19305b828c199d602c23a8337aaa1f03b/tools/server
- https://docs.ollama.com/api/chat
- https://ollama.com/library/qwen3
- https://docs.vast.ai/guides/instances/connect/overview
- https://docs.vast.ai/guides/instances/connect/networking

## Ponytail review

Use only Gunicorn + JSON Schema beyond Python's standard library. One adapter,
one profile, one supervisor. No FastAPI/Pydantic stack, Redis, second queue,
extra proxy or framework. TLS terminates directly or at the existing secure route.
