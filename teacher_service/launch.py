"""Container supervisor. Never starts inference during startup or health checks."""
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

from .app import Application
from .backend import Backend
from .contracts import Failure, PROFILE

STOP = threading.Event()
CHILDREN = []


def stop_children(children, grace=10):
    for child in children:
        if child.poll() is None:
            child.terminate()
    end = time.monotonic() + grace
    for child in children:
        try:
            child.wait(timeout=max(.01, end - time.monotonic()))
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def run_child(command, quiet=False):
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL if quiet else None,
                             stderr=subprocess.DEVNULL if quiet else None)
    CHILDREN.append(child)
    return child


def verified(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            if STOP.is_set():
                raise RuntimeError('stopping')
            digest.update(block)
    return digest.hexdigest() == PROFILE['sha256']


def model_file():
    cache = Path(os.environ.get('TEACHER_MODEL_DIR', '/workspace/models'))
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / PROFILE['filename']
    if target.exists():
        if not verified(target):
            raise RuntimeError('cached_model_checksum_failed')
        return target
    partial = target.with_suffix('.gguf.partial')
    url = f"https://huggingface.co/{PROFILE['model_id']}/resolve/{PROFILE['revision']}/{PROFILE['filename']}"
    print('phase=model_download', flush=True)
    download = run_child(['curl', '--fail', '--location', '--silent', '--proto', '=https',
                          '--proto-redir', '=https', '--connect-timeout', '30', '--max-time', '7200',
                          '--retry', '2', '--retry-delay', '3', '--continue-at', '-', '--output', str(partial), url], quiet=True)
    while download.poll() is None:
        if STOP.wait(.2):
            raise RuntimeError('stopping')
    if download.returncode != 0 or not verified(partial):
        raise RuntimeError('model_download_or_checksum_failed')
    partial.replace(target)
    return target


def backend_command(path):
    return ['/opt/llama/llama-server', '--model', str(path), '--alias', PROFILE['model_id'],
            '--host', '127.0.0.1', '--port', '8081', '--ctx-size', str(PROFILE['context_tokens']),
            '--parallel', '1', '--gpu-layers', 'all', '--fit', 'off', '--no-context-shift',
            '--flash-attn', 'on', '--jinja', '--chat-template-kwargs', '{"enable_thinking":false}',
            '--no-webui', '--slots', '--log-disable']


def gateway_command():
    host = os.environ.get('TEACHER_BIND_HOST', '0.0.0.0')
    args = [sys.executable, '-m', 'gunicorn', 'teacher_service.app:create_app()',
            '--bind', f'{host}:8000', '--workers', '1', '--worker-class', 'gthread',
            '--threads', '4', '--worker-connections', '8', '--timeout', '30',
            '--graceful-timeout', '20', '--keep-alive', '2', '--error-logfile', '-',
            '--log-level', 'warning', '--limit-request-line', '2048', '--limit-request-fields', '32',
            '--limit-request-field_size', '4096']
    cert, key = os.environ.get('TEACHER_TLS_CERT', ''), os.environ.get('TEACHER_TLS_KEY', '')
    if bool(cert) != bool(key):
        raise RuntimeError('tls_pair_required')
    if cert:
        if not Path(cert).is_file() or not Path(key).is_file():
            raise RuntimeError('tls_files_missing')
        args += ['--certfile', cert, '--keyfile', key]
    return args


def main():
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: STOP.set())
    try:
        Application(os.environ.get('TEACHER_API_KEY', ''))  # fail before downloading
        gateway_args = gateway_command()
        print('phase=model_verify', flush=True)
        path = model_file()
        print('phase=model_load', flush=True)
        backend = run_child(backend_command(path), quiet=True)
        deadline = time.monotonic() + 900
        while not STOP.is_set():
            if backend.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError('model_load_failed')
            try:
                Backend().ready()
                break
            except Failure:
                STOP.wait(1)
        if STOP.is_set():
            return 0
        gateway = run_child(gateway_args)
        print('phase=serving', flush=True)
        while not STOP.wait(.5):
            if backend.poll() is not None or gateway.poll() is not None:
                raise RuntimeError('serving_child_exited')
        return 0
    except Exception:
        # Paths, library exceptions and subprocess output may contain secrets.
        print('phase=failed; check profile, cache checksum, GPU/driver, ports and TLS files', flush=True)
        return 1
    finally:
        stop_children(CHILDREN)


if __name__ == '__main__':
    sys.exit(main())
