# Vast.ai / VPS deployment runbook

## Preflight and image

Build/publish with `bash scripts/publish.sh` on an authenticated Docker Buildx
machine. Record the git SHA and returned image digest. This repository does not
contain weights, registry credentials or a published-image guarantee. Do not use
a mutable `latest` tag. OS image tags and apt repositories are mutable; deployment
reproducibility relies on retaining the built image digest. Inspect the build log
and run container tests before publishing a release for live jobs.

The build defaults target CUDA SM 80/86/89/90 (Ampere/Ada/Hopper), not arbitrary
48 GB GPUs. Check GPU architecture and driver compatibility with CUDA 12.8.1.
If the host is Turing/Blackwell or a different architecture, review and rebuild
with a matching `CUDA_ARCHITECTURES` argument; do not claim the current binary fits.
Weight file is ~32.5 GB; allow at least 60 GB free disk for image/cache and prefer
64 GB host RAM. Full GPU offload is requested, automatic fitting/context reduction
is off. OOM exits; there is no CPU/quantization fallback.

## Entrypoint mode (recommended for this image)

Use Vast Entrypoint mode with the immutable image digest and leave its default
entrypoint intact. Supply `TEACHER_API_KEY`, mount persistent `/workspace/models`,
and map TCP container port 8000 if direct TLS is used. Vast assigns the actual
public host port. Supply `TEACHER_TLS_CERT` and `TEACHER_TLS_KEY` pointing to mounted
PEM files whose certificate matches the hostname used by the VPS. The gateway
terminates TLS directly. Private registry pull authentication belongs in Vast's
registry configuration, not the Dockerfile. Never publish backend port 8081.

Model download is resumable at `.gguf.partial`, with at most two curl retries and
a two-hour per-transfer limit. SHA-256 must match before rename. Existing cache
is rehashed on restart; corruption fails closed. Check disk/network if startup
reports `phase=failed`. Replace a confirmed corrupt cache file deliberately;
no automatic destructive deletion or alternative model selection occurs.

Startup phases: model_verify → model_download (only if absent) → model_load →
serving. Liveness may be unavailable until download/load completes. Model load
has a 15-minute deadline. Readiness checks do not generate a label. Serving child
exit stops both children and returns nonzero; configure the instance manager's
restart behavior. Compose uses `unless-stopped`. TERM/INT terminates both children,
then kills after ten seconds. Pending jobs remain owned by the VPS.

## SSH / Jupyter mode

For the private SSH template, publish the tested image first and set its exact
image reference when creating the template:

```bash
export TEACHER_IMAGE_REF=ghcr.io/serda-dev/linguai-teacher-model:COMMIT_SHA
bash scripts/create_vast_template.sh
```

To update an existing Vast template, also set `TEACHER_TEMPLATE_HASH_ID` to its
current hash ID. Vast replaces omitted fields on update; the script sends the
complete definition. Template ID `748997` was created for this service. The
release built from commit `e34702721623778dfd5e13abe2eed187051c5148` is
`ghcr.io/serda-dev/linguai-teacher-model:e347027`, with published manifest-list
digest `sha256:02f84fbe4d5f23ad8d4fd390140a59431e006fe282fa82d581040aabba1e291e`.
The current Vast template points to that tag; verify its digest at deployment.

The template reserves 80 GB disk and starts this repository's launcher through
Vast's SSH-mode onstart script. It binds port 8000 to container loopback and
publishes no API port. Supply `TEACHER_API_KEY` privately when launching the
instance, and configure registry pull credentials if the image is private.
Creating the template neither rents a GPU nor proves the image can be pulled.
Confirm the image digest and GPU compatibility before choosing an offer.

Vast may replace the Docker entrypoint for SSH/Jupyter modes. Do not assume seeing
a notebook means inference is running. This image does not install Jupyter or
an SSH daemon itself; verify Vast's selected mode provides the operator SSH
service. If it does not, use Entrypoint + TLS above, or prepare the operator
channel separately. Once logged into a compatible image environment:

```bash
cd /app
# Supply TEACHER_API_KEY through the instance environment, never a notebook cell.
nohup /opt/venv/bin/python -m teacher_service.launch > /workspace/teacher.log 2>&1 &
```

Use this as a long-lived supervised startup command if restarting the instance;
a one-off shell command does not survive instance recreation. Do not start a
second supervisor while one already runs. With a tunnel, set
`TEACHER_BIND_HOST=127.0.0.1` and leave TLS variables unset on GPU.

From the VPS host, using the actual Vast SSH address and verified host key:

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 -L 127.0.0.1:18000:127.0.0.1:8000 \
  -p GPU_SSH_PORT GPU_SSH_USER@GPU_SSH_HOST
```

Use `TEACHER_BASE_URL=http://127.0.0.1:18000/v1` **only for a caller running on
that same VPS network namespace**. A Coolify Docker worker cannot use host
127.0.0.1: it means its own container. For Coolify, run a supervised SSH tunnel
sidecar on the worker's private Docker network, with no published ports, bind
the tunnel sidecar's forward to `0.0.0.0:18000`, and point the worker at
`http://teacher-tunnel:18000/v1`. Mount only the restricted SSH identity and
verified known_hosts; never disable host key verification. Alternatively use
the direct HTTPS address from the worker, avoiding any tunnel sidecar. Run the
connection check in the same network namespace as the actual worker. The provided
CLI deliberately permits plain HTTP only on loopback; run that check inside the
tunnel sidecar for this private-network topology, and then verify reachability
from the worker before enabling jobs.

## Acceptance on the actual host

Record `nvidia-smi` GPU name/driver/free VRAM, model cache revision/checksum,
image digest, context/output/parallel profile, memory after load and peak during
one approved inference. Measure end-to-end requests from the VPS with
`check_connection.py --request` on an approved tiny A–H set. One invocation sends
at most one completion; the operator controls the approved total. Never log
source text or generated labels. Existing labels remain immutable in the VPS.

Readiness alone does not certify semantic quality, full GPU offload, VRAM headroom,
TLS reachability from Coolify, throughput or latency. Require p95 below the
20-second caller limit with network margin. Current worker lease is 60 seconds
and heartbeat freshness 30 seconds. If this fails, do not hide it by raising only
the GPU timeout: change/test the VPS caller and lease/heartbeat design together
in that repository before accepting long-running jobs.

## Failure handling

| Signal | Meaning / next step |
| --- | --- |
| 401 | GPU/VPS API keys differ or missing |
| 400 context_length_exceeded | Full rendered request exceeds 8192 minus output/safety; review upstream sketch/profile, never silently slice here |
| 429 busy | One generation or cancellation in progress; VPS retry policy owns retry |
| 502 invalid_teacher_label / output_limit | No accepted label; inspect approved calibration/profile, no automatic repair |
| 503 / connection unavailable | Loading, failed child, profile mismatch or route problem |
| 504 backend_timeout | 18-second budget exhausted; measure latency and review coordinated caller limits |

## Official references

- https://docs.vast.ai/guides/instances/connect/overview
- https://docs.vast.ai/guides/instances/connect/networking
- https://docs.vast.ai/guides/templates/introduction
