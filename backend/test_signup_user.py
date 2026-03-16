import requests
import json

url = "http://localhost:8000/auth/signup"
data = {
    "username": "moniii",
    "email": "mr.rolex718@gmail.com",
    "password": "password123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
