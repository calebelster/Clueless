"""Manual check that Firebase Auth and Firestore are connected

The pytest tests fake Firebase, so no real connection
This script uses the real Firebase project. Run it once after setup, or to
test if the connection is broken.

Needs FIREBASE_CREDENTIALS and FIREBASE_WEB_API_KEY set in backend/.env.
Run from backend/:
    uv run python smoke_firebase.py
"""

import os

import requests

from firebase_client import init_firebase
from game import auth, db

# Connect to Firebase using the service account key named in .env
init_firebase()

# Database: write a test game to Firestore, then read it back.
#    Expect: {'ok': True}
db.save_game("smoke-test", {"ok": True})
print("1. Firestore read back:", db.load_game("smoke-test"))

# Get an anonymous ID token from Firebase,  same kind a player gets
key = os.environ["FIREBASE_WEB_API_KEY"]
resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={key}",
    json={"returnSecureToken": True},
    timeout=10,
)
resp.raise_for_status()  # error if Anonymous sign-in is off
token = resp.json()["idToken"]

# Sign-in: send AUTH_REQ token
#    Expect: AUTH_RESP with success True and a long playerId
reply = auth.login({"type": "AUTH_REQ", "sessionToken": token, "payload": {"displayName": "Smoke"}})
print("2. AUTH_RESP:", reply)

# request with the same real token should  accept
#    Expect: accepted, with   playerId
msg, err = auth.authenticate({"type": "MOVE_REQ", "sessionToken": token, "payload": {}})
print("3. Real token:", err or f"accepted playerId={msg['playerId']} name={msg['displayName']}")

# forged token should reject
#    Expect: ACTION_REJECTED with AUTH_INVALID_TOKEN.
_, err = auth.authenticate({"type": "MOVE_REQ", "sessionToken": "forged"})
print("4. Forged token:", err)