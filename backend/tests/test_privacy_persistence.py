"""""
Checks for persistence, serialization,
and private infromation handling

run from backend/:
    uv run pytest tests/test_privacy_persistence.py -v
"""

import json
import threading
from dataclasses import dataclass

import pytest

from game import comm, db
from game.privacy import player_view
from game.serialization import SerializationError, to_storable


def _state(status="in_progress"):
    return {
        "game_id": "g-1",
        "status": status,
        "players": {
            "alice": {"display_name": "Alice", "hand": [{"card_type": "weapon", "name": "Rope"}]},
            "bob": {"display_name": "Bob", "hand": [{"card_type": "room", "name": "Study"},
                                                    {"card_type": "weapon", "name": "Wrench"}]},
        },
        "case_file": {
            "character": {"card_type": "character", "name": "Mr. Green"},
            "weapon": {"card_type": "weapon", "name": "Candlestick"},
            "room": {"card_type": "room", "name": "Ballroom"},
        },
        "turn_order": ["alice", "bob"],
    }


class FakeWS:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(json.loads(text))

@pytest.fixture(autouse=True)
def _clean_connections():
    comm.connections.clear()
    comm.clients.clear()
    yield
    comm.connections.clear()

# ---- Serialization and persistence ----

def test_state_round_trips_unchanged():
    db.save_game("g-1", _state())
    assert db.load_game("g-1") == _state()


def test_objects_with_to_dict_and_dataclasses_are_stored():
    @dataclass
    class Card:
        card_type: str
        name: str

    class Game:
        def to_dict(self):
            return {"status": "lobby", "cards": [Card("weapon", "Rope")]}

    db.save_game("g-2", Game())
    assert db.load_game("g-2") == {"status": "lobby", "cards": [{"card_type": 
                                                                 "weapon", "name": "Rope"}]}

def test_list_inside_list_is_rejected_before_reaching_firestore():
    with pytest.raises(SerializationError):
        to_storable({"board": [["hall", "lounge"]]})

def test_loaded_state_is_a_copy():
    db.save_game("g-1", _state())
    loaded = db.load_game("g-1")
    loaded["status"] = "finished"
    assert db.load_game("g-1")["status"] == "in_progress"


def test_update_game_does_not_lose_concurrent_writes():
    db.save_game("g-1", {"count": 0})

    def bump():
        for _ in range(50):
            db.update_game("g-1", lambda s: s.update(count=s["count"] + 1))

    threads = [threading.Thread(target=bump) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert db.load_game("g-1")["count"] == 200

# ---- Private information ----

def test_viewer_sees_only_own_hand_and_no_case_file():
    view = player_view(_state(), "alice")
    assert view["players"]["alice"]["hand"] == [{"card_type": "weapon", "name": "Rope"}]
    assert "hand" not in view["players"]["bob"]
    assert view["players"]["bob"]["hand_count"] == 2
    assert "case_file" not in view


def test_case_file_revealed_when_game_finished():
    assert "case_file" in player_view(_state("finished"), "alice")


def test_player_view_does_not_edit_stored_state():
    state = _state()
    player_view(state, "alice")
    assert state == _state()

def test_state_broadcast_gives_each_player_only_their_own_hand():
    a, b, stranger = FakeWS(), FakeWS(), FakeWS()
    comm.register("alice", a)
    comm.register("bob", b)
    comm.register("someone-else", stranger)

    comm.deliver(None, [{"to": "game", "game_id": "g-1", "state": _state()}])

    alice_msg, bob_msg = a.sent[0], b.sent[0]
    assert alice_msg["type"] == "GAME_STATE_UPDATE"
    assert "hand" in alice_msg["payload"]["players"]["alice"]
    assert "hand" not in alice_msg["payload"]["players"]["bob"]
    assert "hand" in bob_msg["payload"]["players"]["bob"]
    assert "hand" not in bob_msg["payload"]["players"]["alice"]
    for msg in (alice_msg, bob_msg):
        assert "case_file" not in msg["payload"]
    assert stranger.sent == []  # players outside the game get nothing

def test_private_message_reaches_only_its_player():
    a, b = FakeWS(), FakeWS()
    comm.register("alice", a)
    comm.register("bob", b)

    card = {"type": "CARD_SHOWN", "payload": {"card": {"card_type": "room",
                                                        "name": "Study"}, "shown_by": "bob"}}
    comm.deliver(None, [{"to": "player", "player_id": "alice",
                          "message": card}])

    assert a.sent == [card]
    assert b.sent == []

def test_rejection_goes_only_to_sender():
    sender, other = FakeWS(), FakeWS()
    comm.register("alice", sender)
    comm.register("bob", other)

    msg = {"type": "ACTION_REJECTED", "payload": {"errorCode": "ILLEGAL_ACTION", "reason": "not your turn"}}
    comm.deliver(sender, [{"to": "sender", "message": msg}])

    assert sender.sent == [msg]
    assert other.sent == []

def test_legacy_tuple_broadcast_strips_hands_and_case_file(monkeypatch):
    from game import auth, game_session

    ws = FakeWS()
    comm.clients.append(ws) #monkeypatch allows us to test authentication without touching firebase 
    monkeypatch.setattr(auth, "authenticate",
                        lambda m: ({**m, "playerId": "alice", "displayName": "Alice"}, None))
    monkeypatch.setattr(game_session, "dispatch",
                        lambda m: ({"type": "GAME_STATE_UPDATE", "payload": _state()}, None))

    comm.handle_message(ws, json.dumps({"type": "MOVE_REQ", "sessionToken": "t", "payload": {}}))

    payload = ws.sent[0]["payload"]
    assert all("hand" not in p for p in payload["players"].values())
    assert "case_file" not in payload


def test_disconnect_unregisters_socket():
    ws = FakeWS()
    comm.register("alice", ws)
    comm.unregister(ws)
    assert "alice" not in comm.connections
