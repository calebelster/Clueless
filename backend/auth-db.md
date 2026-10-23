
backend/game/auth.py verifies who sent each message backend/game/auth.py verifies who sent each message

backend/game/db.py stores game state and action history in Firestore (FR-DB-8, FR-DB-9)

#### Using it

After authentication, every message has two verified fields: playerId and displayName. Use these, never IDs or names from the client's payload

```python
from game import db

db.save_game(game_id, state)    # state must be a dict
db.load_game(game_id)           # returns a copy, or None
db.log_action(game_id, action)
db.load_actions(game_id)        # oldest first
```

load_game() returns a copy, so call save_game() to keep changes. 
Firestore can't store a list inside a list, so use dicts for the board and hands.

## Client sign-in

```javascript
import { signIn, withToken } from "./firebaseAuth";

ws.send(JSON.stringify(await signIn("Buchi")));     // once, sends AUTH_REQ
ws.send(JSON.stringify(await withToken(message)));  // every message after
```

### Testing without Firebase
```python
db.use_store(db.MemoryStore())
```

Run the tests from backend/:
""
uv run pytest -v
""

### Communication hookup
Add to handle_message() in comm.py, after parsing:
```python
if msg_type == "AUTH_REQ":
    ws.send(json.dumps(auth.login(message)))
    return
message, rejected = auth.authenticate(message)
if rejected:
    ws.send(json.dumps(rejected))
    return
```

## Connecting to Firebase

Needed only to run the full server.

1. Ask permission to add you as an Editor on the Firebase project.
2. Project settings → Service accounts → Generate new private key.
3. Save it as `backend/serviceAccountKey.json`, run `cp .env.example .env` in `backend/`,
   and set `FIREBASE_WEB_API_KEY` in `.env` (Project settings → General).
4. Run `uv run python smoke_firebase.py` to check the connection.

Never commit or share `.env` or the key file (NFR-SPR-1).
