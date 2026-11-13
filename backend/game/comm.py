"""Communication subsystem: WebSocket connections, routing, and broadcasts."""

import json
import logging
import threading
from datetime import UTC, datetime

from game import auth, db, game_session
from game.privacy import player_view

logger = logging.getLogger(__name__)

# Skeletal implementation: all currently connected WebSockets.
#
# Future increments should associate connections with game IDs so broadcasts
# can be limited to players in the relevant game session.
clients = []

# Authenticated connections: player uid -> set of open sockets (a player may have
# more than one tab open). Filled after a successful AUTH_REQ.
connections = {}
_connections_lock = threading.Lock()

def register(uid, ws):
    """Associate an open socket with a verified player"""
    with _connections_lock:
        connections.setdefault(uid, set()).add(ws)


def unregister(ws):
    """Forget a closed socket. Called by app.py when a client disconnects"""
    with _connections_lock:
        for uid in list(connections):
            connections[uid].discard(ws)
            if not connections[uid]:
                del connections[uid]
    if ws in clients:
        clients.remove(ws)


def send_to_player(uid, message: dict):
    """Send a private message to every socket of one player"""
    with _connections_lock:
        sockets = list(connections.get(uid, ()))
    for ws in sockets:
        send_to_client(ws, message)


def _game_player_ids(game_id, state=None):
    if state is None:
        state = db.load_game(game_id) or {}
    return list((state.get("players") or {}).keys())


def broadcast_state(game_id, state: dict, extra_payload: dict | None = None):
    """
    Send GAME_STATE_UPDATE to each player in the game, each filtered by
    player_view() so nobody receives another player's hand or the Case File
    """
    for uid in _game_player_ids(game_id, state):
        payload = {"gameId": game_id, **player_view(state, uid)}
        if extra_payload:
            payload.update(extra_payload)
        send_to_player(uid, {"type": "GAME_STATE_UPDATE", "payload": payload})


def broadcast_to_game(game_id, message: dict):
    """Send a public message (no private data) to every player in one game."""
    for uid in _game_player_ids(game_id):
        send_to_player(uid, message)


def deliver(ws, envelopes):
    """
    Route Game Session output. Each envelope is one of:
        {"to": "sender", "message": {...}}
        {"to": "player", "player_id": uid, "message": {...}}     # private
        {"to": "game", "game_id": gid, "state": {...}}           # per-player views
        {"to": "game", "game_id": gid, "message": {...}}         # public notice
    """
    for env in envelopes or ():
        to = env.get("to")
        if to == "sender":
            send_to_client(ws, env["message"])
        elif to == "player":
            send_to_player(env["player_id"], env["message"])
        elif to == "game" and "state" in env:
            broadcast_state(env["game_id"], env["state"])
        elif to == "game":
            broadcast_to_game(env["game_id"], env["message"])
        else:
            logger.error("[COMM] dropped envelope with unknown target: %r", to)


 # ---- Legacy Comm.py --- #
def send_to_client(ws, message: dict):
    """Send one message to one connected client"""

    try:
        ws.send(json.dumps(message))
    except Exception:
        logger.exception("[COMM] failed sending message to client")

        if ws in clients:
            clients.remove(ws)


def broadcast(message: dict):
    """Send a message to every connected client and drop dead ones"""

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
    Route one incoming WebSocket message through the server subsystems

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
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )
        return

    # AUTH_REQ is special because the player is not authenticated yet.
    if msg_type == "AUTH_REQ":
        response = auth.login(message)
        payload = response.get("payload") or {}
        if payload.get("success"):
            register(payload["playerId"], ws)
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

    # Re-authenticated sockets (e.g. after a reconnect) are registered again.
    register(authenticated_message["playerId"], ws)

    # Forward the verified request into Game Session.
    result = game_session.dispatch(authenticated_message)

    # New contract: Game Session returns a list of envelopes (see deliver()).
    if isinstance(result, list):
        deliver(ws, result)
        return

    
   # Legacy contract: (state_message, notification). Kept until Game Session
    # moves to envelopes so nothing breaks mid-integration.
    state_message, notification = result

    # Successful game-state changes are broadcast so connected clients
    # demonstrate synchronization during the skeletal increment.
    #
    # ACTION_REJECTED is private and should only go back to the sender.
    if state_message is not None:
        if state_message.get("type") == "GAME_STATE_UPDATE":
            # A shared broadcast cannot be personalised, so strip every hand
            # and the Case File rather than risk leaking them.
            safe = dict(state_message)
            safe["payload"] = player_view(state_message.get("payload") or {}, None)
            broadcast(safe)
        else:
            send_to_client(ws, state_message)

    # Event notifications are currently broadcast to every connected client.
    # A later increment should limit broadcasts to the relevant game session.
    if notification is not None:
        broadcast(notification)