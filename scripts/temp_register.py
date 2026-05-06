import requests
url='http://127.0.0.1:5050/api/auth/register'
payload={'name':'Test User','email':'test_copilot@example.com','password':'TestPass123!'}
resp=requests.post(url,json=payload)
print(resp.status_code)
print(resp.text)
