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

## Client flow

The client supports the minimal game flow:

1. Sign in with a display name using Firebase anonymous authentication.
2. Create a game or join one with its game ID, then pick a character.
3. The host starts the game (3 to 6 players, every player has a character).
4. Click a highlighted board tile to move; the server rejects illegal moves.
5. Suggest from a room; prompted players disprove or pass.
6. Accuse to win; a wrong accusation eliminates the accuser.
7. Game state, events, and rejections update live across all clients.

Suggestion, disprove, and accuse support depends on the backend Rules Engine
integration.

## Message protocol

| Message | Direction | Purpose |
|---|---|---|
| `AUTH_REQ` | Client → Server | Authenticate a player using a Firebase session token and display name |
| `AUTH_RESP` | Server → Client | Return authentication success/failure and verified player information |
| `CREATE_GAME_REQ` | Client → Server | Create a new game session |
| `JOIN_GAME_REQ` | Client → Server | Join an existing game session |
| `SELECT_CHAR_REQ` | Client → Server | Select a character for the authenticated player |
| `START_GAME_REQ` | Client → Server | Start a game session |
| `MOVE_REQ` | Client → Server | Move the player's character to `payload.targetLocationId` |
| `SUGGEST_REQ` | Client → Server | Suggest `payload.character` and `payload.weapon`; the room is implicit (the suggester's current room) |
| `DISPROVE_REQ` | Client → Server | Disprove the current suggestion with `payload.card` (the card as dealt) or `payload.card: null` to pass |
| `ACCUSE_REQ` | Client → Server | Accuse `payload.character`, `payload.weapon`, and `payload.room` |
| `END_TURN_REQ` | Client → Server | End the player's turn |
| `GAME_STATE_UPDATE` | Server → Clients | Broadcast the current shared game-session state |
| `EVENT_LOG_NOTIFICATION` | Server → Clients | Broadcast a game/session event description |
| `ACTION_REJECTED` | Server → Client | Return an authentication, validation, or request error |
| `CHAT_MSG_REQ` | Client → Server | Send the original skeletal chat message |
| `CHAT_BROADCAST` | Server → Clients | Broadcast the original skeletal chat message |

Authenticated messages include a top-level `sessionToken` containing the Firebase ID token. The backend verifies the token before forwarding application requests to the Game Session subsystem.
