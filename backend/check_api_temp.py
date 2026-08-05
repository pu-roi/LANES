import urllib.request
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/reports/active-zones')
    print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
