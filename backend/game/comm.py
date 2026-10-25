"""Communication subsystem: WebSocket connections, routing, and broadcasts."""

import json
import logging
from datetime import datetime, timezone

from game import auth, game_session

logger = logging.getLogger(__name__)

# Skeletal implementation: all currently connected WebSockets.
#
# Future increments should associate connections with game IDs so broadcasts
# can be limited to players in the relevant game session.
clients = []


def send_to_client(ws, message: dict):
    """Send one message to one connected client."""

    try:
        ws.send(json.dumps(message))
    except Exception:
        logger.exception("[COMM] failed sending message to client")

        if ws in clients:
            clients.remove(ws)


def broadcast(message: dict):
    """Send a message to every connected client and drop dead ones."""

    text = json.dumps(message)
    dead = []

    for ws in clients:
        try:
            ws.send(text)
        except Exception:
            dead.append(ws)

    for ws in dead:
        if ws in clients:
            clients.remove(ws)


def handle_message(ws, raw: str):
    """
    Route one incoming WebSocket message through the server subsystems.

    Skeletal flow:

        Client
          -> Communication
          -> Authentication
          -> Game Session
          -> Rules Engine / Database
          -> Communication
          -> Client
    """

    try:
        message = json.loads(raw)

        if not isinstance(message, dict):
            raise TypeError

        msg_type = message["type"]

        if not isinstance(msg_type, str):
            raise TypeError

        payload = message.get("payload", {})

        if not isinstance(payload, dict):
            payload = {}

    except (ValueError, KeyError, TypeError):
        logger.warning("[COMM] bad message: %r", raw)
        return

    logger.info("[COMM] received %s", msg_type)

    # Existing skeletal chat demonstration.
    if msg_type == "CHAT_MSG_REQ":
        broadcast(
            {
                "type": "CHAT_BROADCAST",
                "payload": {
                    "sender": payload.get("sender", "unknown"),
                    "text": payload.get("text", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        )
        return

    # AUTH_REQ is special because the player is not authenticated yet.
    if msg_type == "AUTH_REQ":
        response = auth.login(message)
        send_to_client(ws, response)
        return

    # Every other application request must be authenticated.
    authenticated_message, error = auth.authenticate(message)

    if error is not None:
        send_to_client(ws, error)
        return

    logger.info(
        "[COMM] authenticated %s for player=%s",
        msg_type,
        authenticated_message.get("playerId"),
    )

    # Forward the verified request into Game Session.
    state_message, notification = game_session.dispatch(authenticated_message)

    # Successful game-state changes are broadcast so connected clients
    # demonstrate synchronization during the skeletal increment.
    #
    # ACTION_REJECTED is private and should only go back to the sender.
    if state_message is not None:
        if state_message.get("type") == "GAME_STATE_UPDATE":
            broadcast(state_message)
        else:
            send_to_client(ws, state_message)

    # Event notifications are currently broadcast to every connected client.
    # A later increment should limit broadcasts to the relevant game session.
    if notification is not None:
        broadcast(notification)