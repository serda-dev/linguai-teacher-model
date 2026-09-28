# LinguAI Turkish CPT Teacher Service

A dedicated inference service for the Turkish CPT quality-labeling system. The VPS remains responsible for document storage, run approval, jobs, accepted labels, provenance and exports. This repository owns only the teacher API and model runtime on a replaceable GPU host.

## Current stage

This repository is being prepared for agentic implementation. The authoritative teacher prompt, response schema, caller/API contract, acceptance features, architecture boundaries, unresolved decisions and engineering skills are being established before model-serving code. No model, revision, serving engine, GPU setup or dataset-labeling run is approved by an example value or by the reported 48 GB VRAM alone.

## Start here

1. Read [`AGENTS.md`](AGENTS.md) for the required analyst → architect → developer → tests → audit → version-control workflow.
2. Read [`docs/requirements/README.md`](docs/requirements/README.md) and the authoritative quality specification.
3. Review the architecture, acceptance features and open decisions before selecting a model or adding runtime dependencies.
4. Use the project-specific skills in [`.agents/skills/`](.agents/skills/).

The main API contract is an OpenAI-compatible `POST /v1/chat/completions` call. The caller sends the exact versioned system prompt and a user message containing a document ID and sketch. The completion content must be a JSON string that validates against `schemas/teacher_label_v1.schema.json` and keeps the requested ID. The service must never label documents, fetch a corpus, or write into the VPS database on its own.

GPU installation and model calibration begin only after the operator supplies access to the actual GPU host. A Jupyter/SSH address is not itself an inference API endpoint.
