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
from copy import deepcopy

from proto.marshal.marshal import Rule

from game import db
from game.rules_engine import RulesEngine

from game.game_logic import CharType, CardType, WeaponType, RoomType, Card, Game, Player, CaseFile, Character, GameStatus

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



class ERROR_CODE:
    GAME_NOT_FOUND = "GAME_NOT_FOUND"
    GAME_FULL = "GAME_FULL"
    CHARACTER_UNKNOWN = "CHARACTER_UNKNOWN"
    CHARACTER_TAKEN = "CHARACTER_TAKEN"
    ALREADY_JOINED = "ALREADY_JOINED"
    PLAYER_NOT_IN_GAME = "PLAYER_NOT_IN_GAME"
    NOT_HOST = "NOT_HOST"
    GAME_ALREADY_STARTED = "GAME_ALREADY_STARTED"
    GAME_ENDED = "GAME_ENDED"
    PLAYER_COUNT = "PLAYER_COUNT"
    MISSING_CHARACTER = "MISSING_CHARACTER"
    MISS_SCARLET_REQUIRED = "MISS_SCARLET_REQUIRED"

class ACTION_STATUS:
    ACTION_REJECTED = "ACTION_REJECTED"

UNKNOWN_GAME_ID = "unknown"


rules_engine = RulesEngine()


def _rules_engine_stub(action, game, player, payload):
    return rules_engine.execute(action, game, player, payload)


def _rejected(error_code, reason):
    """
    ACTION_REJECTED (), sent to the sender only NFR-OR-2, NFR, UER-3
    """
    logger.info(f"[GAME] REJECTED: {reason}")
    return {
        "type": ACTION_STATUS.ACTION_REJECTED,
        "payload": {"errorCode": error_code, "reason": reason},
    }


def _load_game(game_id: str) -> Game | None:
    """
    Load a game by game_id from db
    """
    if not game_id:
        return None

    try:
        game_state = db.load_game(game_id)
        if game_state is None:
            return None
        return Game.from_dict(db.load_game(game_id))
    except ValueError:
        return None


def _players_in_turn_order(players: dict[str, Player]):
    """
    Player ids in character order
    """
    order = []
    # Iterate throught the characters in turn order
    for char_type in CharType:
        for player_id, player in players.items():
            assert player.character is not None
            if player.character.name == char_type:
                order.append(player_id)

    assert len(order) == len(players)

    return order


def _setup_game(game_state: Game):
    """
    Sets up the game FR-GS-5, FR-GS-6, FR-GS-7, FR-GS-8
    """

    players = game_state.players
    deck = []

    deck = Card.all_cards()

    # Set up Case File
    character = Card(CardType.CHARACTER.value, random.choice([c for c in CharType]).value)
    weapon = Card(CardType.WEAPON.value, random.choice([w for w in WeaponType]).value)
    room = Card(CardType.ROOM.value, random.choice([r for r in RoomType]).value)
    case_file = CaseFile(room, weapon, character)

    # Shuffle remaining cards
    deck = [card for card in deck if card not in {character, weapon, room}]
    random.shuffle(deck)

    # Create turn order
    turn_order = _players_in_turn_order(game_state.players)

    # Deal the card one at a time in turn order
    for index, card in enumerate(deck):
        player_id = turn_order[index % len(turn_order)]
        players[player_id].add_card(card)

    game_state.case_file = case_file
    game_state.turn_order = turn_order
    game_state.status = GameStatus.STARTED

    start_idx = 0
    for i, id in enumerate(turn_order):
        if game_state.players[id].character.name == CharType.MISS_SCARLET:
            start_idx = i

    game_state.current_turn_index = start_idx


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

    if game_state.suggestion_round:
        current_turn_index = game_state.disprove_turn_index
    else:
        current_turn_index = game_state.current_turn_index

    # stub_state = game_state.get("stubState") or {}
    state_message = {
        "type": "GAME_STATE_UPDATE",
        "payload": {
            "gameId": game_id,
            "status": game_state.status.value,
            "players": {player_id: player.to_dict() for player_id, player in game_state.players.items()},
            "currentTurnPlayer": game_state.turn_order[current_turn_index],
            # "boardLocations": stub_state.get("boardLocations") or {}, TODO - What is this supposed to be?
            # "activeStatus": stub_state.get("activeStatus") or {}, TODO - what is active status supposed to be?
            "turnOrder": game_state.turn_order,
        },
    }
    notification = {
        "type": "EVENT_LOG_NOTIFICATION",
        "payload": {"eventType": event_type, "description": description},
    }
    return state_message, notification


# ======================================Core Functions============================================


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

    host = Player(host_id, display_name)
    game_state = Game(game_id, host)

    current_time = datetime.now(UTC).isoformat()
    # game_state = {
    #     "status": "lobby",
    #     "hostId": host_id,
    #     "createdAt": current_time,
    #     "players": {
    #         host_id: {
    #             "displayName": display_name,
    #             "characterId": None,
    #             "joinedAt": current_time,
    #         }
    #     },
    #     "stubState": {
    #         "currentTurnPlayer": None,
    #         "boardLocations": {},
    #         "activeStatus": {},
    #     },
    # }

    db.save_game(game_id, game_state)
    db.save_player(host_id, display_name, game_id)
    logger.info(f"[GAME] Game created {game_id}, host: {host_id}")

    return _saved(game_id, game_state, "GAME_CREATED", f"{display_name} created {game_id}")


def join_game(game_id, player_id, display_name):
    """
    FR-GS-2
    Join a game session
    """

    # Get game
    if game_id is None:
        pass

    game_state = _load_game(game_id)
    if game_state is None:
        if not game_id:
            game_id = UNKNOWN_GAME_ID
        return _rejected(ERROR_CODE.GAME_NOT_FOUND, f"game {game_id} not found"), None

    # Cannot add players after game has started
    if game_state.status != GameStatus.LOBBY:
        raise NotImplementedError

    # Create player
    player = Player(player_id, display_name)

    # A game can only have at most 6 players
    if player_id not in game_state.players and len(game_state.players) >= MAX_PLAYERS:
        return _rejected(ERROR_CODE.GAME_FULL, "Game has 6 players already"), None
    
    # Player already in game
    if player_id in game_state.players:
        # Do nothing? Throw Error
        return _rejected(ERROR_CODE.ALREADY_JOINED, "Player has already joined game")

    # Add player
    game_state.add_player(player)

    db.save_game(game_id, game_state)
    db.save_player(player_id, display_name, game_id)
    logger.info(f"[GAME] {player_id} joined {game_id} ({len(game_state.players)} players)")

    return _saved(game_id, game_state, "PLAYER_JOINED", f"{display_name} joined {game_id}")


def select_character(player_id: str, character_id: str):
    """
    FR-GS-3
    Save the player's character
    """
    game_id, game_state = find_game_player(player_id)

    if game_id is None:
        return _rejected(ERROR_CODE.PLAYER_NOT_IN_GAME, "Player is not in a game"), None
    if game_state is None:
        if not game_id:
            game_id = UNKNOWN_GAME_ID
        return _rejected(ERROR_CODE.GAME_NOT_FOUND, f"game {game_id} not found"), None

    # player_id is not in the game
    if player_id not in game_state.players:
        return _rejected(ERROR_CODE.PLAYER_NOT_IN_GAME, f"player {player_id} is not in {game_id}"), None
    # character is not one of the six available suspects
    
    try:
        character = Character(character_id.lower())
    except ValueError:
        return _rejected(ERROR_CODE.CHARACTER_UNKNOWN, "Character is not one of the six suspects"), None
    
    # Check if character is already chosen
    for curr_player_id, player in game_state.players.items():
        if curr_player_id != player_id and player.character is not None and player.character.name == character.name:
            return _rejected(ERROR_CODE.CHARACTER_TAKEN, f"{character_id} is already taken"), None

    game_state.players[player_id].set_character(character)

    db.save_game(game_id, game_state)  # Store character

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
            game_id = UNKNOWN_GAME_ID
        return _rejected(ERROR_CODE.GAME_NOT_FOUND, f"game {game_id} not found"), None
    if player_id not in game_state.players:
        return _rejected(ERROR_CODE.PLAYER_NOT_IN_GAME, f"player {player_id} is not in {game_id}"), None
    if player_id != game_state.host:
        return _rejected(ERROR_CODE.NOT_HOST, "Only the player who created the game can start it"), None
    if game_state.status == GameStatus.STARTED:
        return _rejected(ERROR_CODE.GAME_ALREADY_STARTED, "Game has already started"), None
    if game_state.status == GameStatus.ENDED:
        return _rejected(ERROR_CODE.GAME_ENDED, "Game has ended"), None

    if len(game_state.players) < MIN_PLAYERS or len(game_state.players) > MAX_PLAYERS:
        return _rejected(ERROR_CODE.PLAYER_COUNT, "Game needs 3 to 6 players"), None

    has_scarlet = False

    for _, player in game_state.players.items():
        if player.character is None:
            return _rejected(ERROR_CODE.MISSING_CHARACTER, "Every player must select a character"), None
        if player.character.name == CharType.MISS_SCARLET:
            has_scarlet = True

    if not has_scarlet:
        return _rejected(ERROR_CODE.MISS_SCARLET_REQUIRED, "Miss Scarlet must be selected"), None

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
        return _rejected(ERROR_CODE.PLAYER_NOT_IN_GAME, "Player is not in a game"), None
    if game_state is None:
        if not game_id:
            game_id = UNKNOWN_GAME_ID
        return _rejected(ERROR_CODE.GAME_NOT_FOUND, f"game {game_id} not found"), None
    if player_id not in game_state.players:
        return _rejected(ERROR_CODE.PLAYER_NOT_IN_GAME, f"player {player_id} is not in {game_id}"), None

    payload = message.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    player = game_state.players[player_id]
    logger.info(f"[GAME] Looked up {game_id} | {player_id} -> forward {msg_type} to Rules Engine")
    accepted, reason = _rules_engine_stub(msg_type, game_state, player, payload)

    if not accepted:
        error_msg = reason or "Action rejected by rule engine"
        return _rejected("ILLEGAL_ACTION", error_msg), None

    return _saved(game_id, game_state, msg_type, f"{player_id} sent {msg_type}")
