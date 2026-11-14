from datetime import datetime, timezone
import pytest


from game.game import (
    Card, 
    CardType,
    CharType,
    Character, 
    Player, 
    RoomType, 
    WeaponType
)

@pytest.mark.parametrize(
    "data_dict",
    [
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": False,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "5678",
                "display_name": "disp5678",
                "character": Character(CharType.MISS_SCARLET.value).to_dict(),
                "hand": [
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value).to_dict(),
                    Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value).to_dict(),
                    Card(CardType.ROOM.value, RoomType.HALL.value).to_dict()
                ],
                "is_eliminated": False,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": True,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": False,
                "is_connected": True
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value).to_dict(),
                    Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value).to_dict(),
                    Card(CardType.ROOM.value, RoomType.HALL.value).to_dict()
                ],
                "is_eliminated": True,
                "is_connected": True
            }
        ),
    ]
)
def test_load_player(data_dict):
    player = Player(data_dict["player_id"], data_dict["display_name"])
    player.set_character(Character.from_dict(data_dict["character"]))
    for card in data_dict["hand"]:
        player.add_card(Card.from_dict(card))
    player.is_connected = data_dict["is_connected"]
    player.is_eliminated = data_dict["is_eliminated"]

    test_player = Player.from_dict(data_dict)
    
    assert test_player.player_id == player.player_id
    assert test_player.display_name == player.display_name
    if player.character is not None and test_player.character is not None:
        assert test_player.character.get_location() == player.character.get_location()
    else:
        assert test_player.character == player.character

    assert set(test_player.hand) == set(player.hand)
    assert test_player.is_eliminated == player.is_eliminated

@pytest.mark.parametrize(
    "data_dict",
    [
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": False,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "5678",
                "display_name": "disp5678",
                "character": Character(CharType.MISS_SCARLET.value).to_dict(),
                "hand": [
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value).to_dict(),
                    Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value).to_dict(),
                    Card(CardType.ROOM.value, RoomType.HALL.value).to_dict()
                ],
                "is_eliminated": False,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": True,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": False,
                "is_connected": True
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value).to_dict(),
                    Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value).to_dict(),
                    Card(CardType.ROOM.value, RoomType.HALL.value).to_dict()
                ],
                "is_eliminated": True,
                "is_connected": True
            }
        ),
    ]
)
def test_save_player(data_dict):
    player = Player(data_dict["player_id"], data_dict["display_name"])
    player.set_character(Character.from_dict(data_dict["character"]))
    for card in data_dict["hand"]:
        player.add_card(Card.from_dict(card))
    player.is_connected = data_dict["is_connected"]
    player.is_eliminated = data_dict["is_eliminated"]

    out_dict = player.to_dict()

    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict["player_id"] == data_dict["player_id"]
    assert out_dict["display_name"] == data_dict["display_name"]

    out_hand = set([Card.from_dict(card) for card in out_dict["hand"]])
    hand = set([Card.from_dict(card) for card in data_dict["hand"]])

    assert out_hand == hand
    assert out_dict["is_eliminated"] == data_dict["is_eliminated"]
    assert out_dict["is_connected"] == data_dict["is_connected"]


@pytest.mark.parametrize(
    "data_dict",
    [
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": False,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "5678",
                "display_name": "disp5678",
                "character": Character(CharType.MISS_SCARLET.value).to_dict(),
                "hand": [
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value).to_dict(),
                    Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value).to_dict(),
                    Card(CardType.ROOM.value, RoomType.HALL.value).to_dict()
                ],
                "is_eliminated": False,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": True,
                "is_connected": False
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [],
                "is_eliminated": False,
                "is_connected": True
            }
        ),
        (
            {
                "player_id": "1234",
                "display_name": "disp1234",
                "character": Character(CharType.COLONEL_MUSTARD.value).to_dict(),
                "hand": [
                    Card(CardType.WEAPON.value, WeaponType.ROPE.value).to_dict(),
                    Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value).to_dict(),
                    Card(CardType.ROOM.value, RoomType.HALL.value).to_dict()
                ],
                "is_eliminated": True,
                "is_connected": True
            }
        ),
    ]
)
def test_load_save_player(data_dict):
    out_dict = Player.from_dict(data_dict).to_dict()

    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict["player_id"] == data_dict["player_id"]
    assert out_dict["display_name"] == data_dict["display_name"]

    out_hand = set([Card.from_dict(card) for card in out_dict["hand"]])
    hand = set([Card.from_dict(card) for card in data_dict["hand"]])

    assert out_hand == hand
    assert out_dict["is_eliminated"] == data_dict["is_eliminated"]
    assert out_dict["is_connected"] == data_dict["is_connected"]


def test_player_eliminate():
    player = Player("test", "test")
    assert not player.is_eliminated
    player.eliminate()
    assert player.is_eliminated


def test_player_add_card():
    player = Player("test", "test")
    assert len(player.hand) == 0

    cards = [
        Card(CardType.WEAPON.value, WeaponType.ROPE.value),
        Card(CardType.ROOM.value, RoomType.BALLROOM.value)
    ] * 5

    for i in range(10):
        player.add_card(cards[i])
        assert player.hand[-1] == cards[i]
        assert len(player.hand) == i + 1



@pytest.fixture
def player():
    return Player("test", "test")


@pytest.mark.parametrize(
    "hand, weapon, room, character, expected",
    [
        (
            [],
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
            []
        ),
        (
            [
                Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            ],
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
            [
                Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            ]
        ),
        (
            [
                Card(CardType.WEAPON.value, WeaponType.ROPE.value),
                Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            ],
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
            [
                Card(CardType.WEAPON.value, WeaponType.ROPE.value),
                Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            ]
        ),
        (
            [
                Card(CardType.WEAPON.value, WeaponType.REVOLVER.value),
                Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
                Card(CardType.WEAPON.value, WeaponType.LEAD_PIPE.value),
                Card(CardType.CHARACTER.value, CharType.COLONEL_MUSTARD.value),
                Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            ],
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
            [
                Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            ]
        ),
    ]
)
def test_matching_cards(player, hand, weapon, room, character, expected):
    for card in hand:
        player.add_card(card)

    assert set(player.get_matching_cards(weapon, room, character)) == set(expected)
    
