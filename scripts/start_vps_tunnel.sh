#!/usr/bin/env bash
set -euo pipefail

: "${VAST_SSH_HOST:?Set the direct Vast SSH host}"
: "${VAST_SSH_PORT:?Set the direct Vast SSH port}"
: "${VPS_DOCKER_NETWORK:?Set the LinguAI Coolify Docker network}"

identity="${VAST_SSH_IDENTITY:-$HOME/.ssh/linguai_vast_teacher}"
known_hosts="${VAST_KNOWN_HOSTS:-$HOME/.config/linguai/known_hosts}"
test -r "$identity" && test -r "$known_hosts"

if docker container inspect teacher-tunnel >/dev/null 2>&1; then
  echo 'teacher-tunnel already exists; inspect it before replacing' >&2
  exit 1
fi

docker build -q -f deploy/ssh-tunnel.Dockerfile -t linguai-teacher-tunnel:ssh-client .
docker run -d --name teacher-tunnel --network "$VPS_DOCKER_NETWORK" \
  --restart unless-stopped --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$identity,dst=/run/ssh_key,readonly" \
  --mount "type=bind,src=$known_hosts,dst=/run/known_hosts,readonly" \
  linguai-teacher-tunnel:ssh-client -NT \
  -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/run/known_hosts -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -i /run/ssh_key -p "$VAST_SSH_PORT" \
  -L 0.0.0.0:18000:127.0.0.1:8000 "root@$VAST_SSH_HOST"
