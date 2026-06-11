import requests

url = 'http://127.0.0.1:5000/analyze'
text = 'A person hacked my bank account.'
resp = requests.post(url, data={'caseText': text})
print('status', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
