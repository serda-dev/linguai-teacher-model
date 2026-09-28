"""Immutable wire contract, separate from the application's response envelope."""
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
HASHES = {
    'prompts/turkish_cpt_quality_teacher_v2.txt': '6b71a4690559f7f9b01f489aae65872f222def15f9220b7311a9c70169ee3f68',
    'prompts/teacher_user_v1.txt': '4a937cf0e6b4a4337f2b1c7d2580ceaa7301429d8f28ca3eacc9aaa038283a8d',
    'schemas/teacher_label_v1.schema.json': '341c3979893adb38761fe74fad098383ce5aa3dfa417af20c297f58552d053a0',
}
for name, expected in HASHES.items():
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
        raise RuntimeError('contract_integrity_failure')
SYSTEM = (ROOT / 'prompts/turkish_cpt_quality_teacher_v2.txt').read_text()
USER = (ROOT / 'prompts/teacher_user_v1.txt').read_text()
SCHEMA = json.loads((ROOT / 'schemas/teacher_label_v1.schema.json').read_text())
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA)
PROFILE = json.loads((ROOT / 'profiles/qwen3-30b-a3b-q8.json').read_text())
USER_PATTERN = re.compile(re.escape(USER).replace(re.escape('{{doc_id}}'), r'([^\r\n]{1,256})')
                          .replace(re.escape('{{teacher_sketch}}'), r'([\s\S]+)'))


class Failure(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_key')
            result[key] = value
        return result

    def constant(_):
        raise ValueError('nonfinite_number')

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def parse_request(raw):
    try:
        data = strict_json(raw.decode('utf-8'))
        if not isinstance(data, dict) or set(data) - {'model', 'temperature', 'messages', 'stream', 'max_tokens'}:
            raise ValueError()
        if data.get('model') != PROFILE['model_id']:
            raise Failure(400, 'unsupported_model')
        if type(data.get('temperature')) not in (int, float) or data['temperature'] != 0:
            raise ValueError()
        if data.get('stream', False) is not False:
            raise ValueError()
        output = data.get('max_tokens', PROFILE['max_output_tokens'])
        if type(output) is not int or not 1 <= output <= PROFILE['max_output_tokens']:
            raise Failure(400, 'invalid_output_budget')
        messages = data['messages']
        if not isinstance(messages, list) or len(messages) != 2:
            raise ValueError()
        if messages[0] != {'role': 'system', 'content': SYSTEM}:
            raise Failure(400, 'prompt_version_mismatch')
        if not isinstance(messages[1], dict) or set(messages[1]) != {'role', 'content'} or messages[1]['role'] != 'user':
            raise ValueError()
        match = USER_PATTERN.fullmatch(messages[1]['content'])
        if not match or not match[1].strip():
            raise ValueError()
        return messages, match[1], output
    except Failure:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise Failure(400, 'invalid_request') from None


def validate_completion(result, doc_id):
    if not isinstance(result, dict):
        raise Failure(502, 'invalid_backend_response')
    if result.get('truncated') is not False:
        raise Failure(502, 'backend_truncation')
    if result.get('stop_type') == 'limit':
        raise Failure(502, 'output_limit')
    if result.get('stop_type') != 'eos':
        raise Failure(502, 'incomplete_output')
    try:
        content = result['content']
        if not isinstance(content, str):
            raise ValueError()
        label = strict_json(content)
        if not VALIDATOR.is_valid(label) or label['id'] != doc_id:
            raise ValueError()
        return content
    except (ValueError, TypeError, KeyError, RecursionError):
        raise Failure(502, 'invalid_teacher_label') from None
