"""Local llama.cpp adapter; every stage shares one monotonic deadline."""
import http.client
import json
import socket
import time

from .contracts import Failure, PROFILE, SCHEMA, strict_json, validate_completion


class Backend:
    def __init__(self, port=8081):
        self.port = port

    def call(self, path, body=None, deadline=None):
        deadline = deadline or time.monotonic() + 2
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Failure(504, 'backend_timeout')
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=remaining)
        response = None
        try:
            payload = None if body is None else json.dumps(body).encode()
            conn.request('GET' if body is None else 'POST', path, payload,
                         {'Content-Type': 'application/json', 'Connection': 'close'})
            conn.sock.settimeout(max(.001, deadline - time.monotonic()))
            response = conn.getresponse()
            if response.status != 200:
                raise Failure(503 if response.status == 503 else 502, 'backend_unavailable')
            chunks, size = [], 0
            response_socket = response.fp.raw._sock
            # read1 avoids an unbounded read across a slowly arriving response.
            while True:
                if response.isclosed():
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise Failure(504, 'backend_timeout')
                # HTTPConnection may detach its socket for Connection: close.
                response_socket.settimeout(remaining)
                chunk = response.read1(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > 4 * 1024 * 1024:
                    raise Failure(502, 'backend_response_too_large')
                chunks.append(chunk)
            return strict_json(b''.join(chunks).decode('utf-8'))
        except Failure:
            raise
        except (TimeoutError, socket.timeout):
            raise Failure(504, 'backend_timeout') from None
        except (OSError, ValueError, http.client.HTTPException, UnicodeError, RecursionError):
            raise Failure(502, 'backend_unavailable') from None
        finally:
            if response is not None:
                response.close()
            conn.close()

    def ready(self, deadline=None):
        deadline = deadline or time.monotonic() + 2
        try:
            if self.call('/health', deadline=deadline).get('status') != 'ok':
                raise ValueError()
            props = self.call('/props', deadline=deadline)
            if props['default_generation_settings']['n_ctx'] != PROFILE['context_tokens'] or props['total_slots'] != 1:
                raise ValueError()
            models = self.call('/v1/models', deadline=deadline)
            if [x['id'] for x in models['data']] != [PROFILE['model_id']]:
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            raise Failure(503, 'backend_profile_mismatch') from None

    def generate(self, messages, doc_id, output, deadline):
        self.ready(deadline)
        slots = self.call('/slots', deadline=deadline)
        if not isinstance(slots, list) or len(slots) != 1 or slots[0].get('is_processing') is not False:
            raise Failure(429, 'busy')
        rendered = self.call('/apply-template', {
            'messages': messages, 'chat_template_kwargs': {'enable_thinking': False},
        }, deadline)
        if not isinstance(rendered, dict) or not isinstance(rendered.get('prompt'), str):
            raise Failure(502, 'invalid_backend_template')
        data = self.call('/tokenize', {
            'content': rendered['prompt'], 'add_special': True, 'parse_special': True,
        }, deadline)
        tokens = data.get('tokens') if isinstance(data, dict) else None
        if not isinstance(tokens, list) or not tokens or any(type(x) is not int or x < 0 for x in tokens):
            raise Failure(502, 'invalid_backend_tokens')
        if len(tokens) + output + PROFILE['safety_tokens'] > PROFILE['context_tokens']:
            raise Failure(400, 'context_length_exceeded')
        result = self.call('/completion', {
            'prompt': tokens, 'n_predict': output, 'temperature': 0,
            'stream': False, 'json_schema': SCHEMA, 'cache_prompt': False,
            'n_keep': -1, 'seed': 0, 'repeat_penalty': 1.0,
        }, deadline)
        content = validate_completion(result, doc_id)
        return content
