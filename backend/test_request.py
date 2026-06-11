import sys
import json
import requests

BASE = 'http://127.0.0.1:5000'

def check_health():
    try:
        r = requests.get(f'{BASE}/health', timeout=10)
        r.raise_for_status()
        j = r.json()
        if j.get('status') == 'ok':
            print('health: ok')
            return True
        print('health: unexpected response', j)
        return False
    except Exception as e:
        print('health check failed:', e)
        return False

def check_analyze():
    url = f'{BASE}/analyze'
    payload = {'caseText': 'Someone stolen my gold when I was not there at home'}
    try:
        # backend expects form data (request.form.get('caseText'))
        # Retry a few times because the dev server may be reloading
        attempts = 3
        r = None
        for i in range(attempts):
            try:
                r = requests.post(url, data=payload, timeout=30)
                break
            except requests.exceptions.RequestException:
                if i < attempts - 1:
                    import time
                    time.sleep(1)
                    continue
                raise
        r.raise_for_status()
        j = r.json()
        # Basic sanity checks
        assert 'category' in j
        assert 'laws' in j and isinstance(j['laws'], list)
        print('analyze: ok — category=', j.get('category'))
        return True
    except AssertionError as e:
        print('analyze: response missing expected fields')
        print(r.text if 'r' in locals() else '')
        return False
    except Exception as e:
        print('analyze request failed:', e)
        return False

if __name__ == '__main__':
    ok = check_health()
    if not ok:
        print('FAIL: /health failed')
        sys.exit(2)
    ok = check_analyze()
    if not ok:
        print('FAIL: /analyze failed')
        sys.exit(3)
    print('SMOKE TESTS PASSED')
    sys.exit(0)
