"""Container liveness: no authentication or inference; supports local TLS."""
import os
import ssl
import urllib.request

# The loopback probe checks process life, not certificate trust. Remote clients
# must verify TLS normally; scripts/check_connection.py never disables verification.
context = ssl._create_unverified_context() if os.environ.get('TEACHER_TLS_CERT') else None
scheme = 'https' if context else 'http'
with urllib.request.urlopen(f'{scheme}://127.0.0.1:8000/health', context=context, timeout=3) as response:
    assert response.status == 200
