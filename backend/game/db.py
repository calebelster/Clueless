"""
Database subsytem: only place the server reads and writes stored data

Backed by Firestore though firebase. Only the serve touches firestore. CLients are lcoked out of firestore.rules,
which keps hands anc case file hidden (NFS-SPR-3, NFR-SPR-4) and leave the server as 
the only state writer (NFR-OR-4)

Firestore layout
players/{uid}
games/{game_id}
games/{game_id}/actions/{auto}
dispayName,
gameId
full game state (FR-DB-9)
action history (FR-DB-8)

Firstsre cxanot store a list direcrtly inside each other. 
Board and hand data as dicts or as lists of dicts

Tests and local runs without a Firebase key can sawp wih:
    db.use_store(db.MemoryStore())
"""
import copy
import logging
import threading
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

PLAYERS = "players"
GAMES = "games"
ACTIONS = "actions"

class FirestoreStore:
    " Reads and writes Cloud Firestore: Requries init)firebase() to run"

    def __init__(self, client=None):
        if client is None:
            from firebase_admin import firestore

            try:
                client = firestore.client()
            except ValueError as err:
                raise RuntimeError(
                    "Firebase is not initiaitized. Set FIREBASE_CREDENTIALS in backend/.env"
                ) from err
        self._client = client

    def _doc(self, collection, doc_id):
        #Return a reference to one document, e.g. games/game-1.
        return self._client.collection(collection).document(doc_id)
        
    
    # Read one document. Returns a new dict, or None if the document doesn
    def get(self, collection, doc_id): 
        snap = self._doc(collection, doc_id).get()
        return snap.to_dict() if snap.exists else None
    #write one document. merge=false replaces the whole document,
    # true updates only the fields in data and keeps the rest
    def set(self, collection, doc_id, data, merge=False):
        self._doc(collection, doc_id).set(data, merge=merge)

    #add new doc witha tuo id from collection/id
    def append(self, collection, doc_id, sub, data):
        self._doc(collection, doc_id).collection(sub).add(data)

    #returns every document inc ollection/doc_id/dub, sorted by order_by
    def list(self, collection, doc_id, sub, order_by):
        query = self._doc(collection, doc_id).collection(sub).order_by(order_by)
        return [snap.to_dict() for snap in query.stream()]

class MemoryStore:
    # In_Memory stand in for firestore with the same interface. data is lost on restart
    def __init__(self):
        self._docs = {}
        self._subs = {}
        self._lock = threading.Lock() #flask sock runs each client in its own thread

    # Every func deep-copies data going in and coming out, so callers can never
    # change stored data by editing a dict they passed in. 
    def get(self, collection, doc_id):
        with self._lock:
            data = self._docs.get((collection, doc_id))
            return copy.deepcopy(data)

    #Write one document. merge=True updates only the given fields.
    def set(self, collection, doc_id, data, merge=False):
        with self._lock:
            key = (collection, doc_id)
            if merge and key in self._docs:
                self._docs[key].update(copy.deepcopy(data))
            else:
                self._docs[key] = copy.deepcopy(data)

    #add a dcoument to a subcollection
    def append(self, collection, doc_id, sub, data):
        with self._lock:
            self._subs.setdefault((collection, doc_id, sub), []).append(copy.deepcopy(data))

    #returns copt of every docuemnt in subcollection
    def list(self, collection, doc_id, sub, order_by):
        with self._lock:
            items = copy.deepcopy(self._subs.get((collection, doc_id, sub), []))
        return sorted(items,key=lambda  item: item[order_by])

# The store every public function use
_store = None

def use_store(store):
    #Repalcethe base store. Use MemoryStore() int ests
    global _store
    _store = store

#return the active store, conencting to firestore the first time if none was set
def _get_store():
    global _store
    if _store is None:
        _store = FirestoreStore()
    return _store

def _check_id(value, what):
    "firstore doc id must be non mepty strings withour '/"
    if not isinstance(value, str) or not value or "/" in value or value in(".", ".."):
        raise ValueError(f"invalid{what}: {value!r}")

# -- Players ---
#create and update players. leaves field not passed in unchanged
def save_player(uid, display_name, game_id=None):
    _check_id(uid, "player id")
    data= {"displayName": display_name}
    if game_id is not None:
        data["gameId"] = game_id
    _get_store().set(PLAYERS, uid, data, merge=True)
    logger.info("[DB] saved players = %s", uid)

#return the palyer recors or none 
def load_player(uid):
    _check_id(uid, "player id")
    return _get_store().get(PLAYERS, uid)
# -- Games  ---

#replace the stored fame state with state
def save_game( game_id, state):
    _check_id(game_id, "game id")
    if not isinstance(state, dict):
        raise TypeError("game state must be dict")
    _get_store().set(GAMES, game_id, state)
    logger.info("[DB] saved game = %s", game_id)    

#return the fresh copy of game state. 
# editiing retruend dict does not change what is store. Call save_game() to store changes 
def load_game(game_id):
    _check_id(game_id, "game_id")
    state = _get_store().get(GAMES, game_id)
    logger.info("[DB] loadeed game=%s  and found=%s", game_id, state is not None)
    return state


# -- Action history

def log_action(game_id, action):
    _check_id(game_id, "game_id")
    entry = dict(action)
    entry["at"] = datetime.now(UTC)
    _get_store().append(GAMES, game_id, ACTIONS, entry)

def load_actions(game_id):
    #Return the game's action history, oldest first
    _check_id(game_id, "game id")
    return _get_store().list(GAMES, game_id, ACTIONS, order_by="at")