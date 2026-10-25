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

## Run the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite development URL shown in the terminal, typically:

```text
http://localhost:5173
```

The skeletal client connects to the Flask server over WebSocket at:

```text
ws://127.0.0.1:5000/ws
```

## Skeletal client flow

The current skeletal implementation supports end-to-end communication between the React client and the backend subsystems.

A typical test flow is:

1. Sign in with a display name using Firebase anonymous authentication.
2. Create a game or join an existing game using its game ID.
3. Select a character.
4. Start the game.
5. Send representative game actions such as `MOVE_REQ` or `END_TURN_REQ`.
6. Observe `GAME_STATE_UPDATE` and `EVENT_LOG_NOTIFICATION` messages in the client communication log.

The current skeletal increment focuses on subsystem communication and architecture validation rather than full gameplay behavior.

## Message protocol

| Message | Direction | Purpose |
|---|---|---|
| `AUTH_REQ` | Client → Server | Authenticate a player using a Firebase session token and display name |
| `AUTH_RESP` | Server → Client | Return authentication success/failure and verified player information |
| `CREATE_GAME_REQ` | Client → Server | Create a new game session |
| `JOIN_GAME_REQ` | Client → Server | Join an existing game session |
| `SELECT_CHAR_REQ` | Client → Server | Select a character for the authenticated player |
| `START_GAME_REQ` | Client → Server | Start a game session |
| `MOVE_REQ` | Client → Server | Forward a movement action toward the Rules Engine |
| `END_TURN_REQ` | Client → Server | Forward an end-turn action toward the Rules Engine |
| `GAME_STATE_UPDATE` | Server → Clients | Broadcast the current shared game-session state |
| `EVENT_LOG_NOTIFICATION` | Server → Clients | Broadcast a game/session event description |
| `ACTION_REJECTED` | Server → Client | Return an authentication, validation, or request error |
| `CHAT_MSG_REQ` | Client → Server | Send the original skeletal chat message |
| `CHAT_BROADCAST` | Server → Clients | Broadcast the original skeletal chat message |

Authenticated messages include a top-level `sessionToken` containing the Firebase ID token. The backend verifies the token before forwarding application requests to the Game Session subsystem.
