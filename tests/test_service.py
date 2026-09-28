import copy
import io
import json
import subprocess
import sys
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from wsgiref.simple_server import make_server, WSGIRequestHandler

from teacher_service.app import Application, MAX_BODY
from teacher_service.backend import Backend
from teacher_service.contracts import Failure, PROFILE, SCHEMA, SYSTEM, USER
from teacher_service.launch import backend_command, gateway_command, stop_children, verified

KEY = 'a' * 64  # synthetic fixture
LABEL = {'id': 'doc_test', 'type': 'reference', 'q': {'language': 4, 'coherence': 4,
         'information': 4, 'cleanliness': 1, 'structure': 3, 'utility': 2}, 'noise': ['boilerplate_ui']}


def request():
    return {'model': PROFILE['model_id'], 'temperature': 0, 'messages': [
        {'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': USER.replace(
            '{{doc_id}}', 'doc_test').replace('{{teacher_sketch}}', 'Türkçe; DOCUMENT\n<<<DOCUMENT\n korunur.')} ]}


class FakeBackend(Backend):
    def __init__(self):
        self.calls, self.tokens = [], list(range(7136))
        self.result = {'content': json.dumps(LABEL), 'stop_type': 'eos', 'truncated': False}
        self.problem, self.busy, self.ctx = None, False, 8192

    def call(self, path, body=None, deadline=None):
        self.calls.append((path, body))
        if self.problem: raise self.problem
        return {'/health': {'status': 'ok'},
                '/props': {'default_generation_settings': {'n_ctx': self.ctx}, 'total_slots': 1},
                '/v1/models': {'data': [{'id': PROFILE['model_id']}]},
                '/slots': [{'is_processing': self.busy}], '/apply-template': {'prompt': 'rendered'},
                '/tokenize': {'tokens': self.tokens}, '/completion': self.result}[path]


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.app = Application(KEY, self.backend)

    def call(self, data=None, path='/v1/chat/completions', method='POST', auth=KEY, **overrides):
        raw = json.dumps(request() if data is None else data).encode()
        env = {'REQUEST_METHOD': method, 'PATH_INFO': path, 'CONTENT_TYPE': 'application/json',
               'CONTENT_LENGTH': str(len(raw)), 'wsgi.input': io.BytesIO(raw), 'HTTP_AUTHORIZATION': 'Bearer ' + auth}
        env.update(overrides)
        status = []
        body = b''.join(self.app(env, lambda s, h: status.append(int(s[:3]))))
        return status[0], json.loads(body)

    def test_success_boundary_and_independent_scores(self):
        status, envelope = self.call()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(envelope['choices'][0]['message']['content']), LABEL)
        sent = dict(self.backend.calls)
        self.assertEqual(sent['/apply-template']['messages'], request()['messages'])
        self.assertEqual(sent['/completion']['prompt'], self.backend.tokens)
        self.assertEqual(sent['/completion']['json_schema'], SCHEMA)
        self.assertFalse(sent['/completion']['cache_prompt'])

    def test_one_token_over_never_generates(self):
        self.backend.tokens.append(7136)
        status, body = self.call()
        self.assertEqual((status, body['error']['code']), (400, 'context_length_exceeded'))
        self.assertNotIn('/completion', dict(self.backend.calls))

    def test_output_override_and_invalid_budgets(self):
        data = request(); data['max_tokens'] = 512
        self.assertEqual(self.call(data)[0], 200)
        self.assertEqual(dict(self.backend.calls)['/completion']['n_predict'], 512)
        for value in [0, -1, 1025, True, 1.5, '1024']:
            data['max_tokens'] = value
            self.assertEqual(self.call(data)[0], 400)

    def test_auth_precedes_body_and_backend(self):
        class Unreadable:
            def read(self, *_): raise AssertionError('body read')
        self.assertEqual(self.call(auth='wrong', **{'wsgi.input': Unreadable()})[0], 401)
        self.assertEqual(self.backend.calls, [])

    def test_key_fails_closed(self):
        for key in ['', 'short', 'a' * 40 + '\n', 'ş' * 40]:
            with self.assertRaises(ValueError): Application(key)

    def test_oversized_body(self):
        self.assertEqual(self.call(CONTENT_LENGTH=str(MAX_BODY + 1))[0], 413)
        self.assertEqual(self.backend.calls, [])

    def test_exact_body_limit(self):
        raw = json.dumps(request()).encode(); raw += b' ' * (MAX_BODY - len(raw))
        self.assertEqual(self.call(CONTENT_LENGTH=str(MAX_BODY), **{'wsgi.input': io.BytesIO(raw)})[0], 200)

    def test_invalid_length_type_and_short_body(self):
        for kwargs in [{'CONTENT_LENGTH': '-1'}, {'CONTENT_LENGTH': 'abc'}, {'CONTENT_LENGTH': '0'},
                       {'CONTENT_LENGTH': '999999'}, {'CONTENT_TYPE': 'text/plain'}]:
            self.assertGreaterEqual(self.call(**kwargs)[0], 400)
        self.assertEqual(self.backend.calls, [])

    def test_request_contract(self):
        for key, value in [('model', 'other'), ('temperature', 1), ('temperature', False),
                           ('stream', True), ('source_dataset', 'anything'), ('messages', [])]:
            data = request(); data[key] = value
            self.assertEqual(self.call(data)[0], 400)
        data = request(); data['messages'][0]['content'] += 'modified'
        self.assertEqual(self.call(data)[0], 400)
        data = request(); data['messages'][1]['content'] = 'wrong template'
        self.assertEqual(self.call(data)[0], 400)
        self.assertEqual(self.backend.calls, [])

    def test_json_malformed_duplicate_nonfinite(self):
        for raw in [b'{', b'[]', b'{"model":1,"model":2}', b'{"temperature":NaN}', b'\xff']:
            self.assertEqual(self.call(CONTENT_LENGTH=str(len(raw)), **{'wsgi.input': io.BytesIO(raw)})[0], 400)

    def test_invalid_labels_never_repaired_or_echoed(self):
        invalid = ['SECRET_DOC', '```json\n' + json.dumps(LABEL) + '\n```', '{}', json.dumps(LABEL) * 2]
        for mutate in [lambda x: x.update(id='wrong'), lambda x: x.update(route='DROP'),
                       lambda x: x['q'].update(utility=5), lambda x: x['q'].update(coherence=None),
                       lambda x: x.update(noise=['repetition', 'repetition']),
                       lambda x: x.update(noise=['unknown']), lambda x: x.update(type='unknown')]:
            label = copy.deepcopy(LABEL); mutate(label); invalid.append(json.dumps(label))
        for content in invalid:
            self.backend.result['content'] = content
            status, body = self.call()
            self.assertEqual((status, body['error']['code']), (502, 'invalid_teacher_label'))
            self.assertNotIn('SECRET_DOC', json.dumps(body))

    def test_nullable_language_code(self):
        label = copy.deepcopy(LABEL); label['type'] = 'code'; label['q']['language'] = None
        self.backend.result['content'] = json.dumps(label)
        self.assertEqual(self.call()[0], 200)

    def test_truncation_and_output_limit(self):
        for key, value in [('truncated', True), ('stop_type', 'limit'), ('stop_type', 'none')]:
            self.backend.result = {'content': json.dumps(LABEL), 'stop_type': 'eos', 'truncated': False}
            self.backend.result[key] = value
            self.assertEqual(self.call()[0], 502)

    def test_errors_timeouts_no_retries(self):
        for error in [Failure(504, 'backend_timeout'), Failure(503, 'backend_unavailable')]:
            self.backend.calls.clear(); self.backend.problem = error
            self.assertEqual(self.call()[0], error.status)
            self.assertEqual(len(self.backend.calls), 1)
            self.assertFalse(self.app.gate.locked())

    def test_busy_gate_and_draining_backend(self):
        self.app.gate.acquire()
        try:
            self.assertEqual(self.call()[0], 429)
            self.assertEqual(self.backend.calls, [])
        finally: self.app.gate.release()
        self.backend.busy = True
        self.assertEqual(self.call()[0], 429)
        self.assertNotIn('/completion', dict(self.backend.calls))

    def test_health_ready_never_generate(self):
        self.assertEqual(self.call(path='/health', method='GET', auth='')[0], 200)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.call(path='/ready', method='GET')[0], 200)
        self.assertEqual(self.call(path='/v1/models', method='GET')[0], 200)
        self.assertTrue(set(dict(self.backend.calls)) <= {'/health', '/props', '/v1/models'})
        self.backend.ctx = 4096
        self.assertEqual(self.call(path='/ready', method='GET')[0], 503)

    def test_real_http_wsgi_roundtrip(self):
        class Quiet(WSGIRequestHandler):
            def log_message(self, *_): pass
        server = make_server('127.0.0.1', 0, self.app, handler_class=Quiet)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            req = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                data=json.dumps(request()).encode(), headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=2) as response:
                self.assertEqual(json.load(response)['choices'][0]['finish_reason'], 'stop')
        finally:
            server.shutdown(); server.server_close(); thread.join()


class BackendHTTPTests(unittest.TestCase):
    def test_http_read_and_timeout(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self):
                if self.path == '/slow': time.sleep(.15)
                body = b'{"status":"ok"}'
                self.send_response(200); self.send_header('Content-Length', str(len(body))); self.end_headers()
                try: self.wfile.write(body)
                except BrokenPipeError: pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            backend = Backend(server.server_port)
            self.assertEqual(backend.call('/health'), {'status': 'ok'})
            with self.assertRaises(Failure) as caught: backend.call('/slow', deadline=time.monotonic() + .03)
            self.assertEqual(caught.exception.status, 504)
            with self.assertRaises(Failure): backend.call('/health', deadline=time.monotonic() - 1)
        finally:
            server.shutdown(); server.server_close(); thread.join()


class DeploymentTests(unittest.TestCase):
    def test_launcher_profile(self):
        command = backend_command(Path('/models/example.gguf'))
        for flag in ['--no-context-shift', '--log-disable', '--no-webui']: self.assertIn(flag, command)
        for flag, value in [('--fit', 'off'), ('--host', '127.0.0.1'), ('--parallel', '1'), ('--ctx-size', '8192')]:
            self.assertEqual(command[command.index(flag) + 1], value)

    def test_checksum_detects_corruption(self):
        import hashlib
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'model.gguf'; path.write_bytes(b'fixture')
            with patch.dict(PROFILE, sha256=hashlib.sha256(b'fixture').hexdigest()):
                self.assertTrue(verified(path))
                path.write_bytes(b'corrupt'); self.assertFalse(verified(path))

    def test_supervisor_stops_real_child(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        stop_children([child], grace=.5)
        self.assertIsNotNone(child.poll())

    def test_tls_pair_and_one_worker(self):
        with patch.dict('os.environ', {'TEACHER_TLS_CERT': '/missing', 'TEACHER_TLS_KEY': ''}):
            with self.assertRaises(RuntimeError): gateway_command()
        with patch.dict('os.environ', {'TEACHER_TLS_CERT': '', 'TEACHER_TLS_KEY': ''}):
            command = gateway_command()
            self.assertEqual(command[command.index('--workers') + 1], '1')
            self.assertNotIn('--access-logfile', command)


if __name__ == '__main__': unittest.main()
