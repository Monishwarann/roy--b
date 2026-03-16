from models.auth import hash_password
import sys

try:
    hashed = hash_password("testpassword")
    print(f"Hashed: {hashed}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
