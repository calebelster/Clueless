"""Checks for the Communication subsystem: chat round-trip + bad-message guard."""

import json

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
