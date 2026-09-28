"""Run from the VPS. Default: readiness only. --request sends exactly one request."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from teacher_service.contracts import PROFILE, strict_json, parse_request, VALIDATOR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', type=Path, help='Approved one-document OpenAI request JSON; one generation only')
    args = parser.parse_args()
    base = os.environ['TEACHER_BASE_URL'].rstrip('/')
    parsed = urllib.parse.urlparse(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path != '/v1':
        raise ValueError('Use an API base URL ending in /v1 without credentials/query')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')):
        raise ValueError('Use HTTPS or a local SSH tunnel')
    headers = {'Authorization': 'Bearer ' + os.environ['TEACHER_API_KEY'], 'Content-Type': 'application/json'}
    root = base[:-3]
    start = time.monotonic()
    with urllib.request.urlopen(urllib.request.Request(root + '/ready', headers=headers), timeout=20) as response:
        ready = json.load(response)
    if ready.get('profile') != PROFILE['profile_id'] or ready.get('model_revision') != PROFILE['revision']:
        raise ValueError('Endpoint profile does not match repository')
    print('Readiness OK; no inference performed.')
    if args.request:
        raw = args.request.read_bytes()
        _, doc_id, _ = parse_request(raw)
        start = time.monotonic()
        with urllib.request.urlopen(urllib.request.Request(base + '/chat/completions', data=raw, headers=headers), timeout=20) as response:
            envelope = json.load(response)
        label = strict_json(envelope['choices'][0]['message']['content'])
        VALIDATOR.validate(label)
        if label['id'] != doc_id:
            raise ValueError('Label ID mismatch')
        print(f'One response valid; elapsed_seconds={time.monotonic() - start:.3f}. Label text not printed.')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        print(f'Connection/test failed: HTTP {error.code}; response body suppressed.', file=sys.stderr)
        sys.exit(1)
    except Exception:
        print('Connection/test failed; check URL, TLS, key, readiness and request contract.', file=sys.stderr)
        sys.exit(1)
