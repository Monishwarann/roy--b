import requests
import json

url = "http://localhost:8000/auth/signup"
data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
