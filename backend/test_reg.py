import urllib.request
import json
req = urllib.request.Request('http://localhost:8000/api/auth/register', data=json.dumps({'email': 'test@test.com', 'password': '123', 'name': 'Test'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(req)
except Exception as e:
    print(e.read().decode())
