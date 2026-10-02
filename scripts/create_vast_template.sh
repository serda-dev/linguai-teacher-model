#!/usr/bin/env bash
set -euo pipefail

: "${TEACHER_IMAGE_REF:?Set TEACHER_IMAGE_REF to the published Teacher image reference}"
command -v vastai >/dev/null || { echo 'vastai CLI is required' >&2; exit 1; }

# SSH mode replaces the image entrypoint, so launch the service from Vast onstart.
# Port 8000 stays private and is reached through a verified SSH tunnel from VPS.
template_args=(
  --name 'LinguAI Teacher Qwen3-30B-A3B Q8 SSH'
  --image "$TEACHER_IMAGE_REF"
  --repo 'https://github.com/serda-dev/linguai-teacher-model'
  --desc 'Private Turkish CPT Teacher; Qwen3-30B-A3B Q8; SSH tunnel to LinguAI VPS'
  --disk_space 80
  --ssh
  --env '-e TEACHER_BIND_HOST=127.0.0.1 -e TEACHER_MODEL_DIR=/workspace/models'
  --onstart-cmd 'cd /app && nohup /opt/venv/bin/python -m teacher_service.launch > /workspace/teacher.log 2>&1 &'
  --readme 'Private template. Provide TEACHER_API_KEY (at least 32 ASCII characters) privately when launching. Grant Vast pull access if the image is private. The API listens only on container loopback port 8000; use a verified SSH tunnel from the VPS. Check GPU architecture/driver, available VRAM, model checksum, readiness and latency before starting any labeling run. Do not expose port 8000 publicly.'
)

# Vast update replaces omitted fields rather than preserving them. Always send
# the complete template definition when changing its image or other settings.
if [[ -n "${TEACHER_TEMPLATE_HASH_ID:-}" ]]; then
  vastai update template "$TEACHER_TEMPLATE_HASH_ID" "${template_args[@]}"
else
  vastai create template "${template_args[@]}"
fi
