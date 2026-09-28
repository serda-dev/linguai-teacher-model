# Open decisions

| ID | Decision | Why it matters | Owner / evidence required | Status |
| --- | --- | --- | --- | --- |
| Q-01 | Exact teacher model ID and immutable revision | Quality, licensing, memory, speed and output behavior | User; confirm intended model and license | OPEN |
| Q-02 | GPU vendor/model/count, driver, runtime/CUDA and available disk/network | Determines compatible runtime and model fit | Actual Vast.ai instance inspection | OPEN |
| Q-03 | Serving engine and pinned version | OpenAI endpoint, structured output, batching and GPU support | Architect after model/host data | OPEN |
| Q-04 | Quantization/precision and model-loading profile | Can change quality and VRAM use | Actual loading/inference measurements | OPEN |
| Q-05 | Context and input/output-token caps | Must preserve full teacher prompt + bounded sketch; satisfy caller deadline | Existing VPS cap and GPU measurement | OPEN |
| Q-06 | Safe concurrency, queueing and overload status | Memory use and worker retry behavior | Representative load test; single caller baseline | OPEN |
| Q-07 | Inference p95 relative to current 20 s HTTP timeout | A timeout consumes an attempt and may conflict with 60 s lease / 30 s heartbeat | Actual end-to-end test; caller change separately if needed | OPEN |
| Q-08 | Private network/tunnel, HTTPS address, credential provisioning/rotation | Protect document text and prevent public unauthenticated inference | User/network owner | OPEN |
| Q-09 | Approved tiny calibration examples, rights and review labels | Required to judge semantic rubric alignment | User supplies/approves exact set | OPEN |
| Q-10 | Health/readiness path and externally reachable service port | Coolify/proxy and VPS smoke checks | Decide in architecture once framework/engine chosen | OPEN |
| Q-11 | Model-cache persistence and replacement/re-download cost | GPU instance can be destroyed | Host storage limits and rental economics | OPEN |

Never infer Q-01 from `Qwen/Qwen3.5-35B-A3B-FP8`; that name appeared only as an illustrative example. Never infer any of these decisions from a Jupyter URL alone.
