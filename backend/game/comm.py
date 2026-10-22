"""Communication subsystem: connected WebSocket clients, message routing, broadcasts."""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# every connected WebSocket
# it becomes {game_id: [clients]} when game session added
clients = []


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
        clients.remove(ws)


def handle_message(ws, raw: str):
    """Route one incoming message. Log a bad message to prevent crashes."""
    try:
        message = json.loads(raw)
        msg_type = message["type"]
        payload = message.get("payload", {})
    except (ValueError, KeyError, TypeError):
        logger.warning("bad message: %r", raw)
        return

    if msg_type == "CHAT_MSG_REQ":
        broadcast({
            "type": "CHAT_BROADCAST",
            "payload": {
                "sender": payload.get("sender", "unknown"),
                "text": payload.get("text", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
    else:
        logger.info("unhandled message type: %s", msg_type)
