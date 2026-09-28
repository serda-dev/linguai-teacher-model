"""Narrow WSGI API served by one Gunicorn process; never log request content."""
import hmac
import json
import os
import socket
import threading
import time
import uuid
from http import HTTPStatus

from .backend import Backend
from .contracts import Failure, PROFILE, parse_request

MAX_BODY = 1024 * 1024


class Application:
    def __init__(self, api_key, backend=None, deadline_seconds=18):
        if len(api_key) < 32 or not api_key.isascii() or any(c.isspace() for c in api_key):
            raise ValueError('TEACHER_API_KEY must contain at least 32 ASCII characters without whitespace')
        self.api_key, self.backend = api_key.encode(), backend or Backend()
        self.deadline_seconds = deadline_seconds
        self.gate = threading.Lock()

    def __call__(self, environ, start_response):
        try:
            status, data = self.dispatch(environ)
        except Failure as error:
            status, data = error.status, {'error': {'code': error.code, 'message': error.code, 'type': 'teacher_error'}}
        except Exception:
            # Never include exception repr: it may embed document/model text.
            status, data = 500, {'error': {'code': 'internal_error', 'message': 'internal_error', 'type': 'teacher_error'}}
        body = json.dumps(data, ensure_ascii=True, separators=(',', ':')).encode()
        headers = [('Content-Type', 'application/json'), ('Content-Length', str(len(body))), ('Cache-Control', 'no-store')]
        if status == 429:
            headers.append(('Retry-After', '1'))
        start_response(f'{status} {HTTPStatus(status).phrase}', headers)
        return [body]

    def dispatch(self, env):
        method, path = env['REQUEST_METHOD'], env.get('PATH_INFO', '')
        if method == 'GET' and path == '/health':
            return 200, {'status': 'alive'}
        auth = env.get('HTTP_AUTHORIZATION', '').encode('utf-8')
        if not hmac.compare_digest(auth, b'Bearer ' + self.api_key):
            raise Failure(401, 'unauthorized')
        if method == 'GET' and path in ('/ready', '/v1/models'):
            self.backend.ready()
            if path == '/v1/models':
                return 200, {'object': 'list', 'data': [{'id': PROFILE['model_id'], 'object': 'model', 'owned_by': 'Qwen'}]}
            return 200, {'status': 'ready', 'profile': PROFILE['profile_id'], 'model': PROFILE['model_id'],
                         'model_revision': PROFILE['revision'], 'model_sha256': PROFILE['sha256'],
                         'llama_commit': PROFILE['llama_commit'], 'context_tokens': PROFILE['context_tokens'],
                         'max_output_tokens': PROFILE['max_output_tokens'], 'semantic_calibration': 'not_verified'}
        if method != 'POST' or path != '/v1/chat/completions':
            raise Failure(404, 'not_found')
        if env.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json':
            raise Failure(415, 'json_required')
        try:
            size = int(env.get('CONTENT_LENGTH') or '0')
        except ValueError:
            raise Failure(400, 'invalid_length') from None
        if not 0 < size <= MAX_BODY:
            raise Failure(413 if size > MAX_BODY else 400, 'invalid_request_size')
        # Acquire before reading, so slow authenticated bodies cannot queue work.
        if not self.gate.acquire(blocking=False):
            raise Failure(429, 'busy')
        deadline = time.monotonic() + self.deadline_seconds
        try:
            connection = env.get('gunicorn.socket')
            def expire_body():
                try:
                    connection.shutdown(socket.SHUT_RD)
                except OSError:
                    pass
            timer = threading.Timer(3, expire_body) if connection else None
            if timer:
                timer.start()
            try:
                raw = env['wsgi.input'].read(size)
            except OSError:
                raise Failure(408, 'request_body_timeout') from None
            finally:
                if timer:
                    timer.cancel()
            if len(raw) != size:
                raise Failure(400, 'incomplete_request')
            messages, doc_id, output = parse_request(raw)
            content = self.backend.generate(messages, doc_id, output, deadline)
            return 200, {'id': 'chatcmpl-' + uuid.uuid4().hex, 'object': 'chat.completion',
                         'created': int(time.time()), 'model': PROFILE['model_id'],
                         'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': content}, 'finish_reason': 'stop'}]}
        finally:
            self.gate.release()


def create_app():
    return Application(os.environ.get('TEACHER_API_KEY', ''))
