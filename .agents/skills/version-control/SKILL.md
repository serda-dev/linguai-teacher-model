---
name: version-control
description: Keep teacher-service history focused, verified, and explicit about direct pushes and deployment boundaries.
---

# Version Control — LinguAI Teacher

Inspect repository, branch, changed files, diff and tests before any Git operation. Preserve existing work; never force-push, reset, rewrite history or overwrite unrelated files without explicit instruction.

Use focused commits. Before push, summarize scope and data/security/runtime effects, exact tests run/skipped and unresolved decisions. Follow the user's explicit request for direct main pushes or PRs; default to a reviewable branch/PR when no workflow is specified. No code push alone authorizes GPU rental, deployment, model download, paid inference or bulk labeling.

Exclude credentials, notebook links/tokens, `.env`, model weights/caches, document samples and generated labels. Verify the pushed SHA and branch. Never report an unrun model/GPU or production test as passed.
