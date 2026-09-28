# Runtime decisions and remaining measurements

Updated 2026-09-28 under the user's implementation authorization.

| ID | Decision | State |
| --- | --- | --- |
| Q-01 | Official original Qwen3-30B-A3B GGUF; pinned revision and SHA256 in profile; Apache-2.0 | SELECTED |
| Q-02 | Actual GPU model, driver, architecture, free VRAM/RAM/disk | OPEN: inspect rented host |
| Q-03 | Source-built llama.cpp v0.5.0, immutable commit; see ADR 0002 | SELECTED |
| Q-04 | Q8_0, full GPU layers, no automatic fallback | PROVISIONAL: measure fit/quality |
| Q-05 | 8192 context, 1024 output, 32 safety tokens, exact token counting | SAFE_DEFAULT: reject overflow; measure |
| Q-06 | One active generation; no queue/retry; excess 429 | SAFE_DEFAULT: load measurement pending |
| Q-07 | 18 s service vs 20 s caller, 60 s lease, 30 s heartbeat | OPEN: actual p95; coordinated VPS change if needed |
| Q-08 | Direct TLS or verified SSH route; random Bearer key | OPEN: actual address, credentials and certificate/tunnel |
| Q-09 | Tiny human-reviewed A–H semantic calibration | OPEN: approved samples and model measurements |
| Q-10 | /health liveness, authenticated /ready, container port 8000 | SELECTED: Vast public mapping pending |
| Q-11 | Verified model-only cache at /workspace/models | SELECTED: host volume persistence to confirm |
| Q-12 | CUDA Docker build and published immutable image digest | OPEN: Docker/GPU unavailable in authoring environment |

The Qwen3.5 example in the original envelope is not the chosen model. The latest
user explicitly requested Qwen30A3B and a non-vLLM implementation. No class,
quality threshold, prompt text or routing behavior was invented or changed.
