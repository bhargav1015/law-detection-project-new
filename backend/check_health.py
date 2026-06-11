import requests
import sys

try:
    r = requests.get('http://127.0.0.1:5000/health', timeout=5)
    print(r.status_code, r.text)
except Exception as e:
    print('health check failed:', e)
    sys.exit(1)
