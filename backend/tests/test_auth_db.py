"""Core checks for Authentication (FR-AU-1, NFR-SPR-2) and Database (FR-DB-9).

Covers:
    FR-AU-1    A player can sign in with a display name.
    NFR-SPR-2  Requests without a valid session token are rejected.
    FR-DB-9    The server stores and returns the state of each game.

Firebase is faked here, so these tests run without a Firebase key or internet.
Run from backend/:
    brew install uv OR curl -LsSf https://astral.sh/uv/install.sh | sh
    cd backend
    uv sync
    uv run pytest tests/test_auth_db.py -v

"""


import pytest

from game import auth, db


""" Stand-in for Firebase's token check.
   " good " is treated as a valid token for player u1. Anything else is
    rejected the same way Firebase rejects a bad token: by raising ValueError.
"""
def fake_verify(token):
    if token == "good":
        return {"uid": "u1"}
    raise ValueError("bad token")

#Runs before every test so each one starts from a clean slate.
@pytest.fixture(autouse=True)
def setup(monkeypatch):
    # Replace the real Firebase token check with the fake one above.
    monkeypatch.setattr(auth.fb_auth, "verify_id_token", fake_verify)
    # Use an empty in-memory database instead of Firestore.
    db.use_store(db.MemoryStore())
    # Forget any players signed in by an earlier test.
    auth._names.clear()


#Send an AUTH_REQ with the given token and return the server's AUTH_RESP
def sign_in(token="good"):
    return auth.login({"type": "AUTH_REQ", "sessionToken": token, "payload": {"displayName": "Buchi"}})

# ---- Authentication ----


#FR-AU-1: valid token and display name produce a successful AUTH_RESP.
def test_sign_in_works():
    reply = sign_in()
    assert reply["type"] == "AUTH_RESP"
    assert reply["payload"]["success"] is True
    # The player ID must come from the verified token, not from the client.
    assert reply["payload"]["playerId"] == "u1"

#NFR-SPR-2: a forged token is rejected at sign-in and on every later request.
def test_bad_token_is_rejected():
    assert sign_in("forged")["payload"]["success"] is False
    # signed-in player's request still fails if it carries a forged token.
    sign_in()
    msg, error = auth.authenticate({"type": "MOVE_REQ", "sessionToken": "forged"})
    # The request is stopped (msg is None) and the sender gets ACTION_REJECTED.
    assert msg is None and error["type"] == "ACTION_REJECTED"


def test_must_sign_in_first():
    #NFR-SPR-2: a valid token is not enough; the player must send AUTH_REQ first
    msg, error = auth.authenticate({"type": "MOVE_REQ", "sessionToken": "good"})
    # No sign_in() here, so the server has no record of this player.
    assert msg is None and error is not None


def test_cannot_pretend_to_be_another_player():
    #NFR-SPR-2: the server ignores any playerId the client claims."
    sign_in()
    msg, _ = auth.authenticate({"type": "MOVE_REQ", "sessionToken": "good", "playerId": "hacker"})
    # The client claims to be "hacker", but its token belongs to u1.
     # The server overwrites the claim with the verified player.
    assert msg["playerId"] == "u1"
    assert "sessionToken" not in msg

# ---- Database ----
#NFR-DB-9: a saved game state can be loaded back unchanged.
def test_game_saves_and_loads():
    db.save_game("game-1", {"turn": "u1"})
    assert db.load_game("game-1") == {"turn": "u1"}
     # A game that was never saved returns None instead of crashing.
    assert db.load_game("missing") is None

#NFR-DB-9: load_game() returns a copy, so only save_game() changes stored data.
#Without, the Rules Engine could change a game by accident  by
    # editing a state it loaded, with no save_game() call to show it happened.
def test_editing_loaded_state_does_not_change_saved_state():
    db.save_game("game-1", {"turn": "u1"})
    db.load_game("game-1")["turn"] = "u2"
    assert db.load_game("game-1")["turn"] == "u1"