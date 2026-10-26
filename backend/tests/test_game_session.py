"""
Game Session Subsystem Check
The test assumes users are authenticated

Run from backend/:
    .venv/bin/pytest tests/test_game_session.py -v
"""

import pytest
from game import db, game_session


@pytest.fixture(autouse=True)
def setup():
    db.use_store(db.MemoryStore())


def _msg(msg_type, player_id="p1", display_name="HengKuan", **payload):
    return {
        "type": msg_type,
        "playerId": player_id,
        "displayName": display_name,
        "payload": payload,
    }


def test_full_game(monkeypatch):
    """
    walks theough the entire game
    Check a player can create, join, select character, switch to second game, and the actions are forwarded to the rule engine
    """
    seen = {}

    def fake_rules(action, game, player, payload):
        seen["action"] = action
        seen["payload"] = payload
        return True, ""

    monkeypatch.setattr(game_session, "_rules_engine_stub", fake_rules)

    state_message, _notification = game_session.dispatch(_msg("CREATE_GAME_REQ"))
    game_id = state_message["payload"]["gameId"]
    assert db.load_game(game_id)["hostId"] == "p1"
    assert db.load_player("p1")["gameId"] == game_id

    state_message, notification = game_session.dispatch(_msg("JOIN_GAME_REQ", "p2", "Quinton", gameId=game_id))
    assert state_message["type"] == "GAME_STATE_UPDATE"
    assert notification["type"] == "EVENT_LOG_NOTIFICATION"
    assert set(state_message["payload"]["players"]) == {"p1", "p2"}

    # Join second game and lock the the first game
    state_message, _notification = game_session.dispatch(_msg("CREATE_GAME_REQ", "p3", "Caleb"))
    game_id = state_message["payload"]["gameId"]
    state_message, _notification = game_session.dispatch(_msg("JOIN_GAME_REQ", "p2", "Quinton", gameId=game_id))
    assert state_message["type"] == "GAME_STATE_UPDATE"
    assert db.load_player("p2")["gameId"] == game_id

    state_message, _notification = game_session.dispatch(_msg("SELECT_CHAR_REQ", "p2", "Quinton", characterId="Miss Scarlet"))
    assert state_message["payload"]["players"]["p2"]["characterId"] == "Miss Scarlet"

    state_message, _notification = game_session.dispatch(_msg("START_GAME_REQ", "p2", "Quinton", gameId=game_id))
    assert state_message["payload"]["status"] == "started"

    state_message, notification = game_session.dispatch(_msg("MOVE_REQ", "p2", "Quinton", targetLocationId="hall"))
    assert seen["action"] == "MOVE_REQ"
    assert seen["payload"] == {"targetLocationId": "hall"}
    assert state_message["type"] == "GAME_STATE_UPDATE"
    assert notification["payload"]["eventType"] == "MOVE_REQ"


def test_reject_not_exist_game():
    """
    Check that joining a games that doesnt exist return appropirate error message
    """
    state_message, notification = game_session.dispatch(_msg("JOIN_GAME_REQ", "p2", "Quinton", gameId="g-missing"))
    assert notification is None
    assert state_message["type"] == "ACTION_REJECTED"
    assert state_message["payload"]["errorCode"] == "GAME_NOT_FOUND"
    assert "not found" in state_message["payload"]["reason"]



def test_reject_player_not_joined():
    """
    Check that player that is not in game cannot start a game and gets the appropirate error message
    """
    state_message, _notification = game_session.dispatch(_msg("CREATE_GAME_REQ"))
    game_id = state_message["payload"]["gameId"]

    state_message, notification = game_session.dispatch(_msg("START_GAME_REQ", "p9", "Nobody", gameId=game_id))
    assert notification is None
    assert state_message["type"] == "ACTION_REJECTED"
    assert state_message["payload"]["errorCode"] == "PLAYER_NOT_IN_GAME"
