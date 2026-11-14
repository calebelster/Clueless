from datetime import datetime, timezone
import pytest

from game.game import (
    Card, 
    CardType,
    CharType,
    CaseFile, 
    Location,
    Game,
    GameStatus, 
    Player, 
    RoomType,
    WeaponType
)


@pytest.mark.parametrize(
    "",
    []
)
def test_load_game_state():
    pass


@pytest.mark.parametrize(
    "",
    []
)
def test_save_game_state():
    pass


@pytest.mark.parametrize(
    "data_dict",
    [
        (
            {
                "game_id": "1234",
                "status": GameStatus.STARTED.value,
                "players": {
                    "host": Player("host", "host").to_dict()
                },
                "host": "host",
                "case_file": CaseFile(
                    Card(CardType.ROOM.value, RoomType.HALL.value),
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value),
                    Card(CardType.CHARACTER.value, CharType.COLONEL_MUSTARD.value),
                ).to_dict(),
                "turn_order": ["host"],
                "current_turn_index": 0,
                "disprove_turn_index": 0,
                "current_suggestion": None,
                "suggestion_round": False,
                "created_at": datetime.now(timezone.utc)
            }

        )
    ]
)
def test_load_save_game_state(data_dict):
    out_dict = Game.from_dict(data_dict).to_dict()

    assert out_dict["game_id"] == data_dict["game_id"]
    assert out_dict["status"] == data_dict["status"]
    
    assert len(out_dict["players"]) == len(data_dict["players"])
    assert set(out_dict["players"].keys()) == set(data_dict["players"].keys())
    for player_id, player_dict in data_dict["players"].items():
        test_player_dict = out_dict["players"][player_id]
        assert test_player_dict["player_id"] == player_dict["player_id"]
        assert test_player_dict["display_name"] == player_dict["display_name"]
        if player_dict["character"] is not None:
            assert test_player_dict["character"]["name"] == player_dict["character"]["name"]
            assert Location.from_dict(test_player_dict["character"]["location"]) == Location.from_dict(player_dict["character"]["location"])
            assert test_player_dict["character"]["moved_by_suggestion"] == player_dict["character"]["moved_by_suggestion"]
        else:
            assert test_player_dict["character"] == player_dict["character"]
        assert set([Card.from_dict(card) for card in test_player_dict["hand"]]) == set([Card.from_dict(card) for card in player_dict["hand"]])
        assert test_player_dict["is_eliminated"] == player_dict["is_eliminated"]
        assert test_player_dict["is_connected"] == player_dict["is_connected"]
    
    assert out_dict["host"] == data_dict["host"]
    if data_dict["case_file"] is not None:
        assert CaseFile.from_dict(out_dict["case_file"]) == CaseFile.from_dict(data_dict["case_file"])
    else:
        assert out_dict["case_file"] == data_dict["case_file"]

    assert len(out_dict["turn_order"]) == len(data_dict["turn_order"])
    for i in range(len(data_dict["turn_order"])):
        assert out_dict["turn_order"][i] == data_dict["turn_order"][i]

    assert out_dict["current_turn_index"] == data_dict["current_turn_index"]
    assert out_dict["disprove_turn_index"] == data_dict["disprove_turn_index"]

    if data_dict["current_suggestion"] is not None:
        assert len(out_dict["current_suggestion"]) == len(data_dict["current_suggestion"])
        assert set(out_dict["current_suggestion"].keys()) == set(data_dict["current_suggestion"].keys())

        assert Card.from_dict(out_dict["current_suggestion"]["weapon"]) == Card.from_dict(data_dict["current_suggestion"]["weapon"])
        assert Card.from_dict(out_dict["current_suggestion"]["room"]) == Card.from_dict(data_dict["current_suggestion"]["room"])
        assert Card.from_dict(out_dict["current_suggestion"]["character"]) == Card.from_dict(data_dict["current_suggestion"]["character"])
        
        if data_dict["current_suggestion"]["revealed_card"] is not None:
            assert Card.from_dict(out_dict["current_suggestion"]["revealed_card"]) == Card.from_dict(data_dict["current_suggestion"]["revealed_card"])
        else:
            assert out_dict["current_suggestion"]["revealed_card"] == data_dict["current_suggestion"]["revealed_card"]

        assert out_dict["current_suggestion"]["suggester"] == data_dict["current_suggestion"]["suggester"]
        assert out_dict["current_suggestion"]["disprover"] == data_dict["current_suggestion"]["disprover"]
    else:
        assert out_dict["current_suggestion"] == data_dict["current_suggestion"]

    assert out_dict["suggestion_round"] == data_dict["suggestion_round"]
    assert out_dict["created_at"] == data_dict["created_at"]
