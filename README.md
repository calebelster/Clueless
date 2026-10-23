# Clueless

Clue-Less: an online multiplayer version of the board game Clue. Flask server, React client, Firebase auth and Firestore.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python package management (recommended), or Python 3.14 if you prefer pip

## Backend setup (uv)

```bash
cd backend
uv sync
```

This creates `.venv`, installs all dependencies from `uv.lock`, and includes the dev tools (pytest, ruff, requests).

## Backend setup (pip fallback)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Firebase setup (one time)

The server connects to Firebase for authentication and game storage.

1. Download a service account key: Firebase console -> Project settings -> Service accounts -> Generate new private key
2. Save the key file in `backend/`
3. Copy the env template and point it at your key:

```bash
cp .env.example .env
# edit .env so FIREBASE_CREDENTIALS points at your key file
```

The key file is gitignored. Never commit it.

## Run the server

```bash
uv run flask run
```

Then open http://127.0.0.1:5000. The log should show `Firebase connected`. For auto-reload while developing:

```bash
FLASK_DEBUG=1 uv run flask run
```

## Run tests

```bash
uv run pytest
```

## Lint and format

```bash
uv run ruff check .
uv run ruff format .
```

## Try the communication layer

The server currently speaks one message over a WebSocket. Paste this in the browser console (use two tabs to see the broadcast):

```js
const ws = new WebSocket("ws://127.0.0.1:5000/ws");
ws.onmessage = e => console.log(e.data);
ws.onopen = () => ws.send(JSON.stringify({type: "CHAT_MSG_REQ", payload: {sender: "User", text: "hello"}}));
```

Both tabs print a `CHAT_BROADCAST`.

## Message protocol so far

| Message | Direction | Payload |
|---|---|---|
| `CHAT_MSG_REQ` | client to server | `{sender, text}` |
| `CHAT_BROADCAST` | server to all clients | `{sender, text, timestamp}` |

More messages as the other subsystems (game session, rules engine, events) come online.
