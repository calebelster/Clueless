"""Clue-Less server entry point: app setup + the /ws WebSocket endpoint."""

import logging

from flask import Flask
from flask_cors import CORS
from flask_sock import Sock
from simple_websocket import ConnectionClosed

from firebase_client import init_firebase
from game.comm import clients, handle_message

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)  # allow React dev server to call us
sock = Sock(app)

init_firebase()


@sock.route("/ws")
def ws(ws):
    # Register the client, relay messages until they disconnect
    clients.append(ws)
    try:
        while True:
            message = ws.receive()  # blocks until a message arrives
            handle_message(ws, message)
    except ConnectionClosed:
        pass  # client went away, expected
    finally:
        if ws in clients:
            clients.remove(ws)


if __name__ == "__main__":
    app.run(debug=True)
