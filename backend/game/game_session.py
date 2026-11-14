"""
Game Session subsystems:

This subsystem manages the core logic of the game session:
1.Create games (FR-GS-1)
2.Add players to a game (FR-GS-2)
3.Store each player's character selection (FR-GS-3)
4.Start the game (FR-GS-4)

The actions of the player is forwarded to the rule engine for validation:
1. MOVE_REQ
2. SUGGEST_REQ
3. IDISPROVE_REQ
4. ACCUSE_REQ
4. ENT_TURN_REQ

"""

import logging
import random
import uuid
from datetime import UTC, datetime

from game import db, rules_engine

logger = logging.getLogger(__name__)



CHARACTERS = (
    "Miss Scarlet",
    "Colonel Mustard",
    "Mrs. White",
    "Mr. Green",
    "Mrs. Peacock",
    "Professor Plum",
)
WEAPONS = ("Rope", "Lead Pipe", "Knife", "Wrench", "Candlestick", "Revolver")
ROOMS = (
    "Study",
    "Hall",
    "Lounge",
    "Library",
    "Billiard Room",
    "Dining Room",
    "Conservatory",
    "Ballroom",
    "Kitchen",
)

# Hallway each character occupies when the game is initialized
STARTING_HALLWAY = {
    "Miss Scarlet": "hall-lounge",
    "Colonel Mustard": "lounge-dining",
    "Mrs. White": "ballroom-kitchen",
    "Mr. Green": "conservatory-ballroom",
    "Mrs. Peacock": "library-conservatory",
    "Professor Plum": "study-library",
}

MIN_PLAYERS = 3
MAX_PLAYERS = 6

RULES_MESSAGES = (
    "MOVE_REQ",
    "SUGGEST_REQ",
    "DISPROVE_REQ",
    "ACCUSE_REQ",
    "END_TURN_REQ",
)


def _rules_engine_stub(action, game, player, payload):
    return rules_engine.execute(action, game, player, payload)


def _rejected(error_code, reason):
    """
    ACTION_REJECTED (), sent to the sender only NFR-OR-2, NFR, UER-3
    """
    logger.info(f"[GAME] REJECTED: {reason}")
    return {
        "type": "ACTION_REJECTED",
        "payload": {"errorCode": error_code, "reason": reason},
    }
    

def _load_game(game_id):
    """
    Load a game by game_id from db
    """
    if not game_id:
        return None
    
    try:
        return db.load_game(game_id)
    except ValueError:
        return None


def _players_in_turn_order(players):
    """
    Player ids in character order
    """
    order = []
    # Iterate throught the characters in turn order
    for character in CHARACTERS:
        for player_id, info in players.items():
            # When player is found, add player_id to to the turn order
            if info.get("characterId") == character:
                order.append(player_id)
                break
    return order


def _setup_game(game_state):
    """
    Sets up the game FR-GS-5, FR-GS-6, FR-GS-7, FR-GS-8
    """
    
    players = game_state["players"]
    deck = []

    # Set up case file
    case_file = {
        "suspect": random.choice(CHARACTERS),
        "weapon": random.choice(WEAPONS),
        "room": random.choice(ROOMS),
    }
    
    # Put every suspect into the deck except the one hidden in the Case File
    for name in CHARACTERS:
        if name != case_file["suspect"]:
            deck.append({"category": "suspect", "name": name})
    # Put every weapon into the deck except the one hidden in the Case File
    for name in WEAPONS:
        if name != case_file["weapon"]:
            deck.append({"category": "weapon", "name": name})
    # Put every room into the deck except the on hidden in the Case File
    for name in ROOMS:
        if name != case_file["room"]:
            deck.append({"category": "room", "name": name})
    
    # Shuffle the deck
    random.shuffle(deck)

    # Deal the card one at a time in turn order
    order = _players_in_turn_order(players)
    for index, card in enumerate(deck):
        player_id = order[index % len(order)]
        players[player_id].setdefault("hand", []).append(card)

    board = {}
    active = {}
    scarlet = None
    # Put each character in a starting hallway
    for player_id, info in players.items():
        character = info["characterId"]
        board[character] = STARTING_HALLWAY[character]
        active[player_id] = "active"
        if character == "Miss Scarlet":
            scarlet = player_id

    # Save the game state
    game_state["caseFile"] = case_file
    game_state["turnOrder"] = order
    game_state["status"] = "started"
    # Get game stubState, create new it None
    stub = game_state.setdefault("stubState", {})
    # The player who is miss scarlet should move first
    stub["currentTurnPlayer"] = scarlet
    stub["boardLocations"] = board
    stub["activeStatus"] = active


def find_game_player(player_id):
    """
    Find which game a player is in through the player's record
    """
    try:
        record = db.load_player(player_id)
    except ValueError:
        return None, None
    
    if not record or not record.get("gameId"):
        return None, None
    
    game_id = record["gameId"]
    return game_id, _load_game(game_id)


def _saved(game_id, game_state, event_type, description):
    """
    Record actions into the database
    """
    
    db.log_action(game_id, {"type": event_type, "description": description})
    stub_state = game_state.get("stubState") or {}
    state_message = {
        "type": "GAME_STATE_UPDATE",
        "payload": {
            "gameId": game_id,
            "status": game_state.get("status"),
            "players": game_state.get("players", {}),
            "currentTurnPlayer": stub_state.get("currentTurnPlayer"),
            "boardLocations": stub_state.get("boardLocations") or {},
            "activeStatus": stub_state.get("activeStatus") or {},
            "turnOrder": game_state.get("turnOrder") or [],
        },
    }
    notification = {
    "type": "EVENT_LOG_NOTIFICATION",
    "payload": {"eventType": event_type, "description": description},
    }
    return state_message, notification

#======================================Core Functions============================================

def dispatch(message):
    """
    Entry of game session
    Routes each message to the corresponding function
    Called by Communication
    """
    if not isinstance(message, dict):
        return _rejected("MALFORMED_MESSAGE", "message is malformed"), None

    type = message.get("type")
    player_id = message.get("playerId")
    display_name = message.get("displayName") or ""
    payload = message.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    if not isinstance(player_id, str) or not player_id:
        return _rejected("PLAYER_NOT_IN_GAME", "Player is not in a game"), None

    # Create Game
    if type == "CREATE_GAME_REQ":
        return create_game(player_id, display_name)
    # Join game
    if type == "JOIN_GAME_REQ":
        return join_game(payload.get("gameId"), player_id, display_name)
    # Select Character
    if type == "SELECT_CHAR_REQ":
        return select_character(player_id, payload.get("characterId"))
    # Start Game
    if type == "START_GAME_REQ":
        return start_game(payload.get("gameId"), player_id)
    # Forwards mess to rule engine
    if type in RULES_MESSAGES:
        return handle_action(player_id, message)
    return _rejected("INVALID_MESSAGE_TYPE", "message type is invalid"), None


def create_game(host_id, display_name):
    """
    FR-GS-1
    Create a new game session
    """
    game_id = "g-" + uuid.uuid4().hex[:8]
    current_time = datetime.now(UTC).isoformat()
    game_state = {
        "status": "lobby",
        "hostId": host_id,
        "createdAt": current_time,
        "players": {
            host_id: {
                "displayName": display_name,
                "characterId": None,
                "joinedAt": current_time,
            }
        },
        "stubState": {
            "currentTurnPlayer": None,
            "boardLocations": {},
            "activeStatus": {},
        },
    }
    
    db.save_game(game_id, game_state)
    db.save_player(host_id, display_name, game_id)
    logger.info(f"[GAME] Game created {game_id}, host: {host_id}")

    return _saved(game_id, game_state, "GAME_CREATED", f"{display_name} created {game_id}")


def join_game(game_id, player_id, display_name):
    """
    FR-GS-2
    Join a game session
    """
    game_state = _load_game(game_id)
    if game_state is None:
        if not game_id:
            game_id = "unknown"
        return _rejected("GAME_NOT_FOUND", f"game {game_id} not found"), None

    # A game can only have at most 6 player
    players = game_state.setdefault("players", {})
    if player_id not in players and len(players) >= MAX_PLAYERS:
        return _rejected("GAME_FULL", "Game has 6 players already"), None

    players[player_id] = {
        "displayName": display_name,
        "characterId": None,
        "joinedAt": datetime.now(UTC).isoformat(),
    }
    db.save_game(game_id, game_state)
    db.save_player(player_id, display_name, game_id)
    logger.info(f"[GAME] {player_id} joined {game_id} ({len(game_state['players'])} players)")
    
    return _saved(game_id, game_state, "PLAYER_JOINED", f"{display_name} joined {game_id}")


def select_character(player_id, character_id):
    """
    FR-GS-3
    Save the player's character
    """
    game_id, game_state = find_game_player(player_id)
    
    if game_id is None:
        return _rejected("PLAYER_NOT_IN_GAME", "Player is not in a game"), None
    if game_state is None:
        if not game_id:
            game_id = "unknown"
        return _rejected("GAME_NOT_FOUND", f"game {game_id} not found"), None
    
    # player_id is not in the game
    if player_id not in game_state.get("players", {}):
        return _rejected("PLAYER_NOT_IN_GAME", f"player {player_id} is not in {game_id}"), None
    # character is not one of the six available suspects
    if character_id not in CHARACTERS:
        return _rejected("CHARACTER_UNKNOWN", "Character is not one of the six suspects"), None
    
    # Check if character is already chosen
    for other_id, info in game_state["players"].items():
        if other_id != player_id and info.get("characterId") == character_id:
            return _rejected("CHARACTER_TAKEN", f"{character_id} is already taken"), None

    player = game_state["players"][player_id]
    player["characterId"] = character_id
    db.save_game(game_id, game_state) # Store character
    
    logger.info(f"[GAME] {player_id} selected {character_id} in {game_id}")
    
    return _saved(game_id, game_state, "CHARACTER_SELECTED", f"{player_id} selected {character_id}")


def start_game(game_id, player_id):
    """
    FR-GS-4
    Stat the game
    """
    game_state = _load_game(game_id)
    
    if game_state is None:
        if not game_id:
            game_id = "unknown"
        return _rejected("GAME_NOT_FOUND", f"game {game_id} not found"), None
    if player_id not in game_state.get("players", {}):
        return _rejected("PLAYER_NOT_IN_GAME", f"player {player_id} is not in {game_id}"), None
    if player_id != game_state.get("hostId"):
        return _rejected("NOT_HOST", "Only the player who created the game can start it"), None
    if game_state.get("status") == "started":
        return _rejected("GAME_ALREADY_STARTED", "Game has already started"), None

    players = game_state.get("players", {})
    if not MIN_PLAYERS <= len(players) <= MAX_PLAYERS:
        return _rejected("PLAYER_COUNT", "Game needs 3 to 6 players"), None

    # Both starts as false
    missing_character = False
    has_scarlet = False
    
    # Iterate through all players and heck if each player picked a character
    for info in players.values():
        character_id = info.get("characterId")
        if not character_id:
            missing_character = True
        # Check is Miss Scarlet is picked
        if character_id == "Miss Scarlet":
            has_scarlet = True

    if missing_character:
        return _rejected("MISSING_CHARACTER", "Every player must select a character"), None
    if not has_scarlet:
        return _rejected("MISS_SCARLET_REQUIRED", "Miss Scarlet must be selected"), None

    # Set up the game
    _setup_game(game_state)
    # Save game to db
    db.save_game(game_id, game_state)
    logger.info(f"[GAME] {player_id} started {game_id}")
    return _saved(game_id, game_state, "GAME_STARTED", f"{game_id} started")


def handle_action(player_id, message):
    """
    Look up the game and player, then forward to the Rules Engine
    """
    msg_type = message.get("type")
    game_id, game_state = find_game_player(player_id)
    
    if game_id is None:
        return _rejected("PLAYER_NOT_IN_GAME", "Player is not in a game"), None
    if game_state is None:
        if not game_id:
            game_id = "unknown"
        return _rejected("GAME_NOT_FOUND", f"game {game_id} not found"), None
    if player_id not in game_state.get("players", {}):
        return _rejected("PLAYER_NOT_IN_GAME", f"player {player_id} is not in {game_id}"), None

    payload = message.get("payload")
    if not isinstance(payload, dict):
        payload = {}
        
    player = game_state["players"][player_id]
    logger.info(f"[GAME] Looked up {game_id} | {player_id} -> forward {msg_type} to Rules Engine")
    accepted, reason = _rules_engine_stub(msg_type, game_state, player, payload)
    
    if not accepted:
        error_msg = reason or "Action rejected by rule engine"
        return _rejected("ILLEGAL_ACTION", error_msg), None

    return _saved(game_id, game_state, msg_type, f"{player_id} sent {msg_type}")
