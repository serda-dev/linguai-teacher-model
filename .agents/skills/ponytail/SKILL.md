---
name: ponytail
description: Challenge complexity in LinguAI teacher-service implementation and prefer the smallest safe inference path.
---

# Ponytail — LinguAI Teacher

Read the requirements, architecture and existing source before proposing an abstraction. Trace one caller request through auth, request validation, model generation, output validation and response.

Prefer one API process and one selected serving backend unless measured GPU/runtime constraints require another shape. Reuse backend features only behind a small adapter and always validate returned JSON independently. Avoid a second queue, database, corpus downloader, repair system, orchestration framework, plugin system, generalized model registry, control plane or UI for the single current caller.

Require evidence before adding dependencies, services, caching, batching, retries, concurrency or network ports. Keep the VPS as the single durable workflow owner. Explain the smallest complete vertical slice and trade-offs; do not weaken the authoritative prompt/schema to reduce implementation effort.
