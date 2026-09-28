#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TEACHER_REGISTRY_IMAGE:?Set a registry image, e.g. ghcr.io/serda-dev/linguai-teacher-model}"
test -z "$(git status --porcelain)" || { echo 'Commit changes before publishing.' >&2; exit 1; }
revision=$(git rev-parse HEAD)
docker build --target test --tag linguai-teacher:test .
# Uses existing docker login. Credentials are never accepted as command arguments.
# No latest/main tag: deployment must use the emitted immutable digest.
docker buildx build --platform linux/amd64 \
  --build-arg "VCS_REF=$revision" \
  --tag "${TEACHER_REGISTRY_IMAGE}:${revision}" \
  --metadata-file image.metadata.json --push .
python3 - <<'PY'
import json, os
with open('image.metadata.json') as stream:
    digest = json.load(stream)['containerimage.digest']
print(os.environ['TEACHER_REGISTRY_IMAGE'] + '@' + digest)
PY
