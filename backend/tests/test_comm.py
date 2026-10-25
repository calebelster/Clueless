"""Checks for the Communication subsystem: chat round-trip + bad-message guard."""

import json

from game import auth, game_session
from game.comm import clients, handle_message


class FakeWS:
    """Stands in for a WebSocket and records everything sent to it."""

    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)


def test_chat_request_broadcasts_to_all_clients():
    clients.clear()
    a, b = FakeWS(), FakeWS()
    clients.extend([a, b])

    handle_message(a, '{"type": "CHAT_MSG_REQ", "payload": {"sender": "User", "text": "hi"}}')

    assert len(a.sent) == 1 and len(b.sent) == 1
    msg = json.loads(b.sent[0])
    assert msg["type"] == "CHAT_BROADCAST"
    assert msg["payload"]["sender"] == "User"
    assert msg["payload"]["text"] == "hi"


def test_bad_message_does_not_crash():
    clients.clear()
    ws = FakeWS()
    clients.append(ws)

    handle_message(ws, "not json at all")
    handle_message(ws, '{"no": "type here"}')

    assert ws.sent == []  # nothing sent, nothing crashed

def test_auth_request_is_routed_to_authentication(monkeypatch):
    clients.clear()

    sender = FakeWS()
    other = FakeWS()

    clients.extend([sender, other])

    def fake_login(message):
        assert message["type"] == "AUTH_REQ"

        return {
            "type": "AUTH_RESP",
            "payload": {
                "success": True,
                "playerId": "p1",
                "displayName": "Justin",
            },
        }

    monkeypatch.setattr(auth, "login", fake_login)

    handle_message(
        sender,
        json.dumps(
            {
                "type": "AUTH_REQ",
                "sessionToken": "fake-token",
                "payload": {
                    "displayName": "Justin",
                },
            }
        ),
    )

    assert len(sender.sent) == 1
    assert len(other.sent) == 0

    response = json.loads(sender.sent[0])

    assert response["type"] == "AUTH_RESP"
    assert response["payload"]["success"] is True


def test_authenticated_game_request_reaches_game_session(monkeypatch):
    clients.clear()

    sender = FakeWS()
    other = FakeWS()

    clients.extend([sender, other])

    def fake_authenticate(message):
        assert message["type"] == "MOVE_REQ"

        return (
            {
                "type": "MOVE_REQ",
                "playerId": "p1",
                "displayName": "Justin",
                "payload": {
                    "targetLocationId": "hall",
                },
            },
            None,
        )

    def fake_dispatch(message):
        assert message["playerId"] == "p1"

        return (
            {
                "type": "GAME_STATE_UPDATE",
                "payload": {
                    "gameId": "g-test",
                    "status": "started",
                    "players": {
                        "p1": {
                            "displayName": "Justin",
                        }
                    },
                },
            },
            {
                "type": "EVENT_LOG_NOTIFICATION",
                "payload": {
                    "eventType": "MOVE_REQ",
                    "description": "p1 sent MOVE_REQ",
                },
            },
        )

    monkeypatch.setattr(auth, "authenticate", fake_authenticate)
    monkeypatch.setattr(game_session, "dispatch", fake_dispatch)

    handle_message(
        sender,
        json.dumps(
            {
                "type": "MOVE_REQ",
                "sessionToken": "fake-token",
                "payload": {
                    "targetLocationId": "hall",
                },
            }
        ),
    )

    # Both connected clients get:
    #   GAME_STATE_UPDATE
    #   EVENT_LOG_NOTIFICATION
    assert len(sender.sent) == 2
    assert len(other.sent) == 2

    messages = [json.loads(message) for message in sender.sent]

    assert messages[0]["type"] == "GAME_STATE_UPDATE"
    assert messages[1]["type"] == "EVENT_LOG_NOTIFICATION"


def test_authentication_failure_is_private(monkeypatch):
    clients.clear()

    sender = FakeWS()
    other = FakeWS()

    clients.extend([sender, other])

    def fake_authenticate(message):
        return (
            None,
            {
                "type": "ACTION_REJECTED",
                "payload": {
                    "errorCode": "AUTH_INVALID_TOKEN",
                    "reason": "missing token",
                },
            },
        )

    monkeypatch.setattr(auth, "authenticate", fake_authenticate)

    handle_message(
        sender,
        json.dumps(
            {
                "type": "MOVE_REQ",
                "payload": {},
            }
        ),
    )

    assert len(sender.sent) == 1
    assert len(other.sent) == 0

    response = json.loads(sender.sent[0])

    assert response["type"] == "ACTION_REJECTED"